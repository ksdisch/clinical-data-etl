"""Tests for the ingestion loaders."""

import pandas as pd
import pytest

from clinical_data_etl.ingestion.loaders import (
    DATA_DIR,
    TABLE_CONFIG,
    load_and_merge,
    validate,
)
from clinical_data_etl.ingestion.schemas import ProviderSchema

# ── load_and_merge ───────────────────────────────────────────────────


class TestLoadAndMerge:
    def test_beneficiary_merges_train_test(self):
        df = load_and_merge("beneficiary")
        assert len(df) > 0
        assert "BeneID" in df.columns

    def test_provider_has_fraud_column_after_merge(self):
        """Test split has no PotentialFraud — merge should add it as NaN."""
        df = load_and_merge("providers")
        assert "PotentialFraud" in df.columns
        # Some rows should have NaN (from Test split)
        assert df["PotentialFraud"].isna().any()
        # Some rows should have values (from Train split)
        assert df["PotentialFraud"].notna().any()

    def test_inpatient_merges(self):
        df = load_and_merge("inpatient_claims")
        assert len(df) > 0
        assert "ClaimID" in df.columns
        assert "AdmissionDt" in df.columns

    def test_outpatient_merges(self):
        df = load_and_merge("outpatient_claims")
        assert len(df) > 0
        assert "ClaimID" in df.columns
        assert "AdmissionDt" not in df.columns

    def test_invalid_table_name_raises(self):
        with pytest.raises(KeyError):
            load_and_merge("nonexistent_table")

    def test_all_tables_have_train_and_test_files(self):
        """Verify every configured table has matching files on disk."""
        for table_name, (train_glob, test_glob, _) in TABLE_CONFIG.items():
            train_files = sorted(DATA_DIR.glob(train_glob))
            test_files = sorted(DATA_DIR.glob(test_glob))
            assert len(train_files) > 0, f"No train files for {table_name}"
            assert len(test_files) > 0, f"No test files for {table_name}"


# ── validate ─────────────────────────────────────────────────────────


class TestValidate:
    def test_valid_data_passes(self):
        df = pd.DataFrame([{
            "Provider": "PRV0001",
            "PotentialFraud": "Yes",
        }])
        valid, rejected = validate(df, ProviderSchema, "test_providers")
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_invalid_rows_rejected(self):
        df = pd.DataFrame([
            {"Provider": "PRV0001", "PotentialFraud": "Yes"},
            {"Provider": "PRV0001", "PotentialFraud": "No"},  # Duplicate
        ])
        valid, rejected = validate(df, ProviderSchema, "test_providers")
        # Unique constraint should cause rejection
        assert len(valid) + len(rejected) <= 2


# ── Integration (requires Docker PostgreSQL) ─────────────────────────


class TestIngestionIntegration:
    """End-to-end tests that require a running PostgreSQL instance."""

    @pytest.fixture(autouse=True)
    def _check_db(self):
        """Skip if PostgreSQL is not available."""
        try:
            from clinical_data_etl.utils.db import test_connection
            test_connection()
        except Exception:
            pytest.skip("PostgreSQL not available — run `make db-up`")

    def test_run_ingestion_loads_all_tables(self):
        from sqlalchemy import text

        from clinical_data_etl.ingestion.loaders import run_ingestion
        from clinical_data_etl.utils.db import get_engine

        summary = run_ingestion()

        assert set(summary.keys()) == {
            "beneficiary",
            "inpatient_claims",
            "outpatient_claims",
            "providers",
        }

        engine = get_engine()
        with engine.connect() as conn:
            for table_name, counts in summary.items():
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM raw.{table_name}")
                )
                db_count = result.scalar()
                assert db_count == counts["loaded"], (
                    f"raw.{table_name}: expected {counts['loaded']}, got {db_count}"
                )
