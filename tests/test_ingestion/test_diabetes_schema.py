"""Tests for the diabetes-readmission schema and the '?' recode helper."""

import pandas as pd
import pandera as pa
import pytest

from clinical_data_etl.ingestion.loaders import clean_diabetes_frame, validate
from clinical_data_etl.ingestion.schemas import (
    _DIABETES_MED_COLS,
    DiabetesEncounterSchema,
)


def _valid_diabetes_row() -> dict:
    """One fully-valid encounter row using source (pre-clean) column names.

    encounter_id/patient_nbr are ints (as in the CSV) to exercise str coercion.
    """
    row = {
        "encounter_id": 2278392,
        "patient_nbr": 8222157,
        "race": "Caucasian",
        "gender": "Female",
        "age": "[70-80)",
        "weight": None,
        "admission_type_id": 6,
        "discharge_disposition_id": 1,
        "admission_source_id": 7,
        "time_in_hospital": 3,
        "payer_code": None,
        "medical_specialty": "InternalMedicine",
        "num_lab_procedures": 41,
        "num_procedures": 0,
        "num_medications": 13,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 0,
        "diag_1": "250.83",
        "diag_2": "403",
        "diag_3": "V27",
        "number_diagnoses": 9,
        "max_glu_serum": None,
        "A1Cresult": ">7",
        "change": "Ch",
        "diabetesMed": "Yes",
        "readmitted": "NO",
    }
    # All 23 medication columns default to "No" (a valid value).
    for med in _DIABETES_MED_COLS:
        row[med] = "No"
    row["insulin"] = "Steady"
    return row


def test_valid_row_passes_and_coerces_ids():
    df = pd.DataFrame([_valid_diabetes_row()])
    result = DiabetesEncounterSchema.validate(df)
    assert len(result) == 1
    # coerce=True turns the int id into a string natural key
    assert isinstance(result.loc[0, "encounter_id"], str)


def test_clean_diabetes_frame_recodes_question_mark():
    df = pd.DataFrame([{"race": "?", "gender": "Male", "weight": "[50-75)"}])
    cleaned = clean_diabetes_frame(df)
    assert pd.isna(cleaned.loc[0, "race"])
    # non-sentinel values are untouched
    assert cleaned.loc[0, "gender"] == "Male"
    assert cleaned.loc[0, "weight"] == "[50-75)"


def test_question_mark_race_becomes_null_and_validates():
    """A '?' in a nullable column must validate as NULL after the recode."""
    row = _valid_diabetes_row()
    row["race"] = "?"
    df = clean_diabetes_frame(pd.DataFrame([row]))
    result = DiabetesEncounterSchema.validate(df)
    assert pd.isna(result.loc[0, "race"])


def test_invalid_readmitted_raises():
    row = _valid_diabetes_row()
    row["readmitted"] = "MAYBE"
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        DiabetesEncounterSchema.validate(df, lazy=True)


def test_invalid_medication_value_raises():
    row = _valid_diabetes_row()
    row["insulin"] = "Maybe"
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        DiabetesEncounterSchema.validate(df, lazy=True)


def test_invalid_age_bracket_raises():
    row = _valid_diabetes_row()
    row["age"] = "75"  # not a bracket
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        DiabetesEncounterSchema.validate(df, lazy=True)


def test_validate_quarantines_duplicate_encounter_id():
    """The validate() wrapper splits valid vs rejected on a unique violation."""
    good = _valid_diabetes_row()
    dupe = _valid_diabetes_row()  # same encounter_id -> unique violation
    df = pd.DataFrame([good, dupe])
    valid, rejected = validate(df, DiabetesEncounterSchema, "test_diabetes_dupe")
    assert len(valid) + len(rejected) == 2
    assert len(rejected) >= 1
