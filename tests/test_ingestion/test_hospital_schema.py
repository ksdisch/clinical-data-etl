"""Tests for the hospital-admissions schema, the '20-Nov' recode, and the
surrogate-key minting (tertiary source)."""

import pandas as pd
import pandera as pa
import pytest

from clinical_data_etl.ingestion.loaders import (
    _hospital_surrogate_key,
    clean_hospital_frame,
    validate,
)
from clinical_data_etl.ingestion.schemas import HospitalAdmissionSchema


def _valid_hospital_row() -> dict:
    """One valid admission using source (pre-clean) column names.

    case_id/patientid are ints (as in the CSV) to exercise str coercion. Stay is
    the corrupted '20-Nov' to exercise the recode. No admission_id — it is minted
    by clean_hospital_frame.
    """
    return {
        "case_id": 784,
        "Hospital_code": 25,
        "Hospital_type_code": "b",
        "City_Code_Hospital": 2,
        "Hospital_region_code": "Y",
        "Available Extra Rooms in Hospital": 4,
        "Department": "gynecology",
        "Ward_Type": "Q",
        "Ward_Facility_Code": "D",
        "Bed Grade": 4,
        "patientid": 91534,
        "City_Code_Patient": 8,
        "Type of Admission": "Trauma",
        "Severity of Illness": "Moderate",
        "Visitors with Patient": 2,
        "Age": "41-50",
        "Admission_Deposit": 5356,
        "Stay": "20-Nov",
    }


def test_valid_row_passes_and_coerces_ids():
    df = clean_hospital_frame(pd.DataFrame([_valid_hospital_row()]))
    result = HospitalAdmissionSchema.validate(df)
    assert len(result) == 1
    # coerce=True turns the int ids/labels into strings
    assert isinstance(result.loc[0, "case_id"], str)
    assert isinstance(result.loc[0, "patientid"], str)
    assert isinstance(result.loc[0, "admission_id"], str)


def test_clean_recodes_20_nov_in_age_and_stay():
    row = _valid_hospital_row()
    row["Age"] = "20-Nov"  # Excel-corrupted '11-20' in both columns
    row["Stay"] = "20-Nov"
    cleaned = clean_hospital_frame(pd.DataFrame([row]))
    assert cleaned.loc[0, "Age"] == "11-20"
    assert cleaned.loc[0, "Stay"] == "11-20"
    # a non-corrupted bracket is untouched
    other = clean_hospital_frame(
        pd.DataFrame([{**_valid_hospital_row(), "Stay": "51-60"}])
    )
    assert other.loc[0, "Stay"] == "51-60"


def test_recoded_bracket_validates():
    """A '20-Nov' Stay must validate as '11-20' after the recode."""
    df = clean_hospital_frame(pd.DataFrame([_valid_hospital_row()]))
    result = HospitalAdmissionSchema.validate(df)
    assert result.loc[0, "Stay"] == "11-20"


def test_surrogate_key_deterministic():
    assert _hospital_surrogate_key(784, 91534) == _hospital_surrogate_key(784, 91534)
    # int vs str inputs hash the same (the loader builds it from the raw frame)
    assert _hospital_surrogate_key(784, 91534) == _hospital_surrogate_key(
        "784", "91534"
    )


def test_surrogate_key_minted_and_unique_across_distinct_pairs():
    rows = [
        _valid_hospital_row(),
        {**_valid_hospital_row(), "case_id": 829, "patientid": 41456},
    ]
    cleaned = clean_hospital_frame(pd.DataFrame(rows))
    assert cleaned["admission_id"].notna().all()
    assert cleaned["admission_id"].is_unique


def test_invalid_admission_type_raises():
    row = _valid_hospital_row()
    row["Type of Admission"] = "Walk-in"
    df = clean_hospital_frame(pd.DataFrame([row]))
    with pytest.raises(pa.errors.SchemaErrors):
        HospitalAdmissionSchema.validate(df, lazy=True)


def test_invalid_stay_bracket_raises():
    row = _valid_hospital_row()
    row["Stay"] = "999"  # not a known bracket (and not the recodable artifact)
    df = clean_hospital_frame(pd.DataFrame([row]))
    with pytest.raises(pa.errors.SchemaErrors):
        HospitalAdmissionSchema.validate(df, lazy=True)


def test_nullable_bed_grade_passes():
    row = _valid_hospital_row()
    row["Bed Grade"] = None  # 31 such nulls exist in the real source
    df = clean_hospital_frame(pd.DataFrame([row]))
    result = HospitalAdmissionSchema.validate(df)
    assert pd.isna(result.loc[0, "Bed Grade"])


def test_validate_quarantines_duplicate_admission():
    """Two rows with the same (case_id, patientid) mint the same admission_id —
    the validate() wrapper must split them into valid vs rejected on the unique
    violation."""
    good = _valid_hospital_row()
    dupe = _valid_hospital_row()  # identical business key -> duplicate admission_id
    df = clean_hospital_frame(pd.DataFrame([good, dupe]))
    valid, rejected = validate(df, HospitalAdmissionSchema, "test_hospital_dupe")
    assert len(valid) + len(rejected) == 2
    assert len(rejected) >= 1
