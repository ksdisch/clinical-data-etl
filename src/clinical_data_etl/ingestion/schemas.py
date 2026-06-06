"""Pandera schemas for claims_fraud dataset validation."""

import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema

# --- Chronic condition columns (all int, values 1 or 2) ---
_CHRONIC_CONDITION_COLS = [
    "ChronicCond_Alzheimer",
    "ChronicCond_Heartfailure",
    "ChronicCond_KidneyDisease",
    "ChronicCond_Cancer",
    "ChronicCond_ObstrPulmonary",
    "ChronicCond_Depression",
    "ChronicCond_Diabetes",
    "ChronicCond_IschemicHeart",
    "ChronicCond_Osteoporasis",
    "ChronicCond_rheumatoidarthritis",
    "ChronicCond_stroke",
]

# --- Diagnosis code columns (str, nullable) ---
_DIAGNOSIS_COLS = [f"ClmDiagnosisCode_{i}" for i in range(1, 11)]

# --- Procedure code columns (str, nullable) ---
_PROCEDURE_COLS = [f"ClmProcedureCode_{i}" for i in range(1, 7)]


def _chronic_condition_columns() -> dict[str, Column]:
    return {
        col: Column(int, pa.Check.isin([1, 2]), nullable=False)
        for col in _CHRONIC_CONDITION_COLS
    }


def _nullable_str_columns(names: list[str]) -> dict[str, Column]:
    return {col: Column(str, nullable=True) for col in names}


def _nonneg_int(*, nullable: bool = False) -> Column:
    return Column(int, pa.Check.ge(0), nullable=nullable)


BeneficiarySchema = DataFrameSchema(
    columns={
        "BeneID": Column(str, nullable=False, unique=True),
        "DOB": Column(str, nullable=False),
        "DOD": Column(str, nullable=True),
        "Gender": Column(int, nullable=False),
        "Race": Column(int, nullable=False),
        "RenalDiseaseIndicator": Column(str, nullable=False),
        "State": Column(int, nullable=False),
        "County": Column(int, nullable=False),
        "NoOfMonths_PartACov": Column(int, nullable=False),
        "NoOfMonths_PartBCov": Column(int, nullable=False),
        **_chronic_condition_columns(),
        "IPAnnualReimbursementAmt": Column(float, pa.Check.ge(0), nullable=False),
        "IPAnnualDeductibleAmt": Column(float, pa.Check.ge(0), nullable=False),
        "OPAnnualReimbursementAmt": Column(float, pa.Check.ge(0), nullable=False),
        "OPAnnualDeductibleAmt": Column(float, pa.Check.ge(0), nullable=False),
    },
    coerce=True,
)

InpatientClaimSchema = DataFrameSchema(
    columns={
        "BeneID": Column(str, nullable=False),
        "ClaimID": Column(str, nullable=False, unique=True),
        "ClaimStartDt": Column(str, nullable=False),
        "ClaimEndDt": Column(str, nullable=False),
        "Provider": Column(str, nullable=False),
        "InscClaimAmtReimbursed": Column(float, pa.Check.ge(0), nullable=False),
        "AttendingPhysician": Column(str, nullable=True),
        "OperatingPhysician": Column(str, nullable=True),
        "OtherPhysician": Column(str, nullable=True),
        "AdmissionDt": Column(str, nullable=False),
        "ClmAdmitDiagnosisCode": Column(str, nullable=True),
        "DeductibleAmtPaid": Column(float, nullable=True),
        "DischargeDt": Column(str, nullable=False),
        "DiagnosisGroupCode": Column(str, nullable=True),
        **_nullable_str_columns(_DIAGNOSIS_COLS),
        **_nullable_str_columns(_PROCEDURE_COLS),
    },
    coerce=True,
)

OutpatientClaimSchema = DataFrameSchema(
    columns={
        "BeneID": Column(str, nullable=False),
        "ClaimID": Column(str, nullable=False, unique=True),
        "ClaimStartDt": Column(str, nullable=False),
        "ClaimEndDt": Column(str, nullable=False),
        "Provider": Column(str, nullable=False),
        "InscClaimAmtReimbursed": Column(float, pa.Check.ge(0), nullable=False),
        "AttendingPhysician": Column(str, nullable=True),
        "OperatingPhysician": Column(str, nullable=True),
        "OtherPhysician": Column(str, nullable=True),
        "ClmAdmitDiagnosisCode": Column(str, nullable=True),
        "DeductibleAmtPaid": Column(float, nullable=True),
        **_nullable_str_columns(_DIAGNOSIS_COLS),
        **_nullable_str_columns(_PROCEDURE_COLS),
    },
    coerce=True,
)

ProviderSchema = DataFrameSchema(
    columns={
        "Provider": Column(str, nullable=False, unique=True),
        "PotentialFraud": Column(str, nullable=True),
    },
    coerce=True,
)


# ─────────────────────────────────────────────────────────────────────
# Tertiary source: Synthetic hospital admissions (Kaggle amulyas/synthetic-
# hospital-data — the AV Healthcare Analytics II length-of-stay dataset).
# Single CSV, grain = one hospital admission. Two source quirks are recoded by
# the loader BEFORE validation (see clean_hospital_frame):
#   * the source has NO usable primary key — `case_id` is recycled across
#     unrelated admissions, so a deterministic surrogate `admission_id`
#     (md5 of the unique (case_id, patientid) business key) is minted at ingest;
#   * `Age`/`Stay` carry the literal "20-Nov", an Excel auto-date corruption of
#     the "11-20" bracket, which is recoded back to "11-20".
# Column names keep their source form (incl. spaces) here; the dbt staging model
# renames to snake_case — same split as the diabetes source.
# ─────────────────────────────────────────────────────────────────────

# Age is binned into 10-year brackets ("11-20" after the 20-Nov recode).
_HOSPITAL_AGE_BRACKETS = [
    "0-10",
    "11-20",
    "21-30",
    "31-40",
    "41-50",
    "51-60",
    "61-70",
    "71-80",
    "81-90",
    "91-100",
]

# Length-of-stay brackets: the age brackets plus an open-ended top bucket.
_HOSPITAL_STAY_BRACKETS = [*_HOSPITAL_AGE_BRACKETS, "More than 100 Days"]


HospitalAdmissionSchema = DataFrameSchema(
    columns={
        # Surrogate key minted at ingest (md5 of the unique case_id+patientid pair).
        "admission_id": Column(str, nullable=False, unique=True),
        # Recycled source label (NOT unique) + patient id — kept as degenerate dims.
        "case_id": Column(str, nullable=False),
        "patientid": Column(str, nullable=False),
        # Hospital attributes (degenerate dims — codes are randomized, no clean FD).
        "Hospital_code": Column(int, nullable=False),
        "Hospital_type_code": Column(
            str, pa.Check.isin(["a", "b", "c", "d", "e", "f", "g"]), nullable=False
        ),
        "City_Code_Hospital": Column(int, nullable=False),
        "Hospital_region_code": Column(
            str, pa.Check.isin(["X", "Y", "Z"]), nullable=False
        ),
        "Available Extra Rooms in Hospital": _nonneg_int(),
        "Department": Column(
            str,
            pa.Check.isin(
                [
                    "TB & Chest disease",
                    "anesthesia",
                    "gynecology",
                    "radiotherapy",
                    "surgery",
                ]
            ),
            nullable=False,
        ),
        "Ward_Type": Column(
            str, pa.Check.isin(["P", "Q", "R", "S", "T"]), nullable=False
        ),
        "Ward_Facility_Code": Column(
            str, pa.Check.isin(["A", "B", "C", "D", "E", "F"]), nullable=False
        ),
        # Nullable in source (31 nulls); 1–4 ordinal bed quality grade.
        "Bed Grade": Column(float, pa.Check.isin([1.0, 2.0, 3.0, 4.0]), nullable=True),
        "City_Code_Patient": Column(float, pa.Check.ge(1), nullable=True),
        "Type of Admission": Column(
            str, pa.Check.isin(["Emergency", "Trauma", "Urgent"]), nullable=False
        ),
        "Severity of Illness": Column(
            str, pa.Check.isin(["Minor", "Moderate", "Extreme"]), nullable=False
        ),
        "Visitors with Patient": _nonneg_int(),
        "Age": Column(str, pa.Check.isin(_HOSPITAL_AGE_BRACKETS), nullable=False),
        "Admission_Deposit": Column(float, pa.Check.ge(0), nullable=False),
        # Analytical target — length-of-stay bracket.
        "Stay": Column(str, pa.Check.isin(_HOSPITAL_STAY_BRACKETS), nullable=False),
    },
    coerce=True,
)


# ─────────────────────────────────────────────────────────────────────
# Secondary source: Diabetes readmission (UCI 130-US-hospitals, 1999–2008)
# Single CSV, grain = one hospital encounter. The '?' missing sentinel is
# recoded to NA by the loader BEFORE validation, so nullable columns pass.
# ─────────────────────────────────────────────────────────────────────

# 23 medication columns; each value is one of {No, Steady, Up, Down}.
_DIABETES_MED_COLS = [
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide-metformin",
    "glipizide-metformin",
    "glimepiride-pioglitazone",
    "metformin-rosiglitazone",
    "metformin-pioglitazone",
]

# Age is binned into 10-year brackets in the source.
_AGE_BRACKETS = [
    "[0-10)",
    "[10-20)",
    "[20-30)",
    "[30-40)",
    "[40-50)",
    "[50-60)",
    "[60-70)",
    "[70-80)",
    "[80-90)",
    "[90-100)",
]

_MED_VALUES = ["No", "Steady", "Up", "Down"]


def _medication_columns() -> dict[str, Column]:
    return {
        col: Column(str, pa.Check.isin(_MED_VALUES), nullable=False)
        for col in _DIABETES_MED_COLS
    }


DiabetesEncounterSchema = DataFrameSchema(
    columns={
        "encounter_id": Column(str, nullable=False, unique=True),
        "patient_nbr": Column(str, nullable=False),
        "race": Column(str, nullable=True),
        "gender": Column(
            str, pa.Check.isin(["Female", "Male", "Unknown/Invalid"]), nullable=False
        ),
        "age": Column(str, pa.Check.isin(_AGE_BRACKETS), nullable=False),
        "weight": Column(str, nullable=True),
        "admission_type_id": Column(int, pa.Check.in_range(1, 8), nullable=False),
        "discharge_disposition_id": Column(int, pa.Check.ge(1), nullable=False),
        "admission_source_id": Column(int, pa.Check.ge(1), nullable=False),
        "time_in_hospital": _nonneg_int(),
        "payer_code": Column(str, nullable=True),
        "medical_specialty": Column(str, nullable=True),
        "num_lab_procedures": _nonneg_int(),
        "num_procedures": _nonneg_int(),
        "num_medications": _nonneg_int(),
        "number_outpatient": _nonneg_int(),
        "number_emergency": _nonneg_int(),
        "number_inpatient": _nonneg_int(),
        "diag_1": Column(str, nullable=True),
        "diag_2": Column(str, nullable=True),
        "diag_3": Column(str, nullable=True),
        "number_diagnoses": _nonneg_int(),
        "max_glu_serum": Column(
            str, pa.Check.isin(["Norm", ">200", ">300"]), nullable=True
        ),
        "A1Cresult": Column(str, pa.Check.isin(["Norm", ">7", ">8"]), nullable=True),
        **_medication_columns(),
        "change": Column(str, pa.Check.isin(["No", "Ch"]), nullable=False),
        "diabetesMed": Column(str, pa.Check.isin(["Yes", "No"]), nullable=False),
        "readmitted": Column(str, pa.Check.isin(["NO", ">30", "<30"]), nullable=False),
    },
    coerce=True,
)
