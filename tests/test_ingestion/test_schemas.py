"""Tests for pandera schema validation."""

import pandas as pd
import pandera as pa
import pytest

from clinical_data_etl.ingestion.schemas import (
    BeneficiarySchema,
    InpatientClaimSchema,
    OutpatientClaimSchema,
    ProviderSchema,
)

# ── Beneficiary ──────────────────────────────────────────────────────


def _valid_beneficiary_row() -> dict:
    return {
        "BeneID": "BENE0001",
        "DOB": "1940-01-01",
        "DOD": None,
        "Gender": 1,
        "Race": 1,
        "RenalDiseaseIndicator": "0",
        "State": 10,
        "County": 100,
        "NoOfMonths_PartACov": 12,
        "NoOfMonths_PartBCov": 12,
        "ChronicCond_Alzheimer": 1,
        "ChronicCond_Heartfailure": 2,
        "ChronicCond_KidneyDisease": 1,
        "ChronicCond_Cancer": 2,
        "ChronicCond_ObstrPulmonary": 1,
        "ChronicCond_Depression": 2,
        "ChronicCond_Diabetes": 1,
        "ChronicCond_IschemicHeart": 2,
        "ChronicCond_Osteoporasis": 1,
        "ChronicCond_rheumatoidarthritis": 2,
        "ChronicCond_stroke": 1,
        "IPAnnualReimbursementAmt": 1000.0,
        "IPAnnualDeductibleAmt": 200.0,
        "OPAnnualReimbursementAmt": 500.0,
        "OPAnnualDeductibleAmt": 100.0,
    }


def test_beneficiary_valid():
    df = pd.DataFrame([_valid_beneficiary_row()])
    result = BeneficiarySchema.validate(df)
    assert len(result) == 1


def test_beneficiary_nullable_dod():
    """DOD should accept null values (patient still alive)."""
    row = _valid_beneficiary_row()
    row["DOD"] = None
    df = pd.DataFrame([row])
    result = BeneficiarySchema.validate(df)
    assert len(result) == 1


def test_beneficiary_rejects_negative_reimbursement():
    row = _valid_beneficiary_row()
    row["IPAnnualReimbursementAmt"] = -500.0
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        BeneficiarySchema.validate(df, lazy=True)


def test_beneficiary_rejects_invalid_chronic_condition():
    row = _valid_beneficiary_row()
    row["ChronicCond_Alzheimer"] = 3  # Only 1 or 2 are valid
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        BeneficiarySchema.validate(df, lazy=True)


def test_beneficiary_rejects_null_beneid():
    row = _valid_beneficiary_row()
    row["BeneID"] = None
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        BeneficiarySchema.validate(df, lazy=True)


def test_beneficiary_rejects_duplicate_beneid():
    row1 = _valid_beneficiary_row()
    row2 = _valid_beneficiary_row()  # Same BeneID
    df = pd.DataFrame([row1, row2])
    with pytest.raises(pa.errors.SchemaErrors):
        BeneficiarySchema.validate(df, lazy=True)


# ── Inpatient Claims ─────────────────────────────────────────────────


def _valid_inpatient_row() -> dict:
    row: dict = {
        "BeneID": "BENE0001",
        "ClaimID": "CLM0001",
        "ClaimStartDt": "2009-01-01",
        "ClaimEndDt": "2009-01-10",
        "Provider": "PRV0001",
        "InscClaimAmtReimbursed": 5000.0,
        "AttendingPhysician": "PHY0001",
        "OperatingPhysician": None,
        "OtherPhysician": None,
        "AdmissionDt": "2009-01-01",
        "ClmAdmitDiagnosisCode": "4019",
        "DeductibleAmtPaid": 1068.0,
        "DischargeDt": "2009-01-10",
        "DiagnosisGroupCode": "194",
    }
    for i in range(1, 11):
        row[f"ClmDiagnosisCode_{i}"] = "4019" if i <= 2 else None
    for i in range(1, 7):
        row[f"ClmProcedureCode_{i}"] = "9904" if i == 1 else None
    return row


def test_inpatient_valid():
    df = pd.DataFrame([_valid_inpatient_row()])
    result = InpatientClaimSchema.validate(df)
    assert len(result) == 1


def test_inpatient_rejects_negative_reimbursement():
    row = _valid_inpatient_row()
    row["InscClaimAmtReimbursed"] = -100.0
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        InpatientClaimSchema.validate(df, lazy=True)


def test_inpatient_rejects_null_claim_id():
    row = _valid_inpatient_row()
    row["ClaimID"] = None
    df = pd.DataFrame([row])
    with pytest.raises(pa.errors.SchemaErrors):
        InpatientClaimSchema.validate(df, lazy=True)


# ── Outpatient Claims ────────────────────────────────────────────────


def _valid_outpatient_row() -> dict:
    row: dict = {
        "BeneID": "BENE0001",
        "ClaimID": "CLM0002",
        "ClaimStartDt": "2009-03-01",
        "ClaimEndDt": "2009-03-01",
        "Provider": "PRV0002",
        "InscClaimAmtReimbursed": 200.0,
        "AttendingPhysician": "PHY0002",
        "OperatingPhysician": None,
        "OtherPhysician": None,
        "ClmAdmitDiagnosisCode": "4019",
        "DeductibleAmtPaid": 0.0,
    }
    for i in range(1, 11):
        row[f"ClmDiagnosisCode_{i}"] = "25000" if i == 1 else None
    for i in range(1, 7):
        row[f"ClmProcedureCode_{i}"] = None
    return row


def test_outpatient_valid():
    df = pd.DataFrame([_valid_outpatient_row()])
    result = OutpatientClaimSchema.validate(df)
    assert len(result) == 1


def test_outpatient_has_no_admission_columns():
    """Outpatient schema should not expect admission-specific columns."""
    row = _valid_outpatient_row()
    df = pd.DataFrame([row])
    assert "AdmissionDt" not in df.columns
    assert "DischargeDt" not in df.columns
    assert "DiagnosisGroupCode" not in df.columns
    OutpatientClaimSchema.validate(df)


# ── Provider ─────────────────────────────────────────────────────────


def test_provider_valid_with_fraud_label():
    df = pd.DataFrame([{"Provider": "PRV0001", "PotentialFraud": "Yes"}])
    result = ProviderSchema.validate(df)
    assert len(result) == 1


def test_provider_valid_with_null_fraud_label():
    """Test split providers have no fraud label — should validate with NaN."""
    df = pd.DataFrame([{"Provider": "PRV0001", "PotentialFraud": None}])
    result = ProviderSchema.validate(df)
    assert len(result) == 1


def test_provider_rejects_duplicate_provider():
    df = pd.DataFrame(
        [
            {"Provider": "PRV0001", "PotentialFraud": "Yes"},
            {"Provider": "PRV0001", "PotentialFraud": "No"},
        ]
    )
    with pytest.raises(pa.errors.SchemaErrors):
        ProviderSchema.validate(df, lazy=True)


def test_provider_rejects_null_provider_id():
    df = pd.DataFrame([{"Provider": None, "PotentialFraud": "Yes"}])
    with pytest.raises(pa.errors.SchemaErrors):
        ProviderSchema.validate(df, lazy=True)
