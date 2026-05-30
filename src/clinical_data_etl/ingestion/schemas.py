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
