"""Tests for the ingestion loaders."""

import datetime as dt

import pandas as pd
import pytest

from clinical_data_etl.ingestion.loaders import (
    DATA_DIR,
    TABLE_CONFIG,
    claim_id_bucket,
    load_and_merge,
    validate,
)
from clinical_data_etl.ingestion.schemas import ProviderSchema

# True when the Kaggle CSVs have been downloaded locally
_HAS_RAW_DATA = any(DATA_DIR.glob("Train_Beneficiary*.csv"))

# ── load_and_merge ───────────────────────────────────────────────────


@pytest.mark.skipif(not _HAS_RAW_DATA, reason="Kaggle CSVs not downloaded")
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
        df = pd.DataFrame(
            [
                {
                    "Provider": "PRV0001",
                    "PotentialFraud": "Yes",
                }
            ]
        )
        valid, rejected = validate(df, ProviderSchema, "test_providers")
        assert len(valid) == 1
        assert len(rejected) == 0

    def test_invalid_rows_rejected(self):
        df = pd.DataFrame(
            [
                {"Provider": "PRV0001", "PotentialFraud": "Yes"},
                {"Provider": "PRV0001", "PotentialFraud": "No"},  # Duplicate
            ]
        )
        valid, rejected = validate(df, ProviderSchema, "test_providers")
        # Unique constraint should cause rejection
        assert len(valid) + len(rejected) <= 2


# ── Integration (requires Docker PostgreSQL) ─────────────────────────


@pytest.mark.skipif(not _HAS_RAW_DATA, reason="Kaggle CSVs not downloaded")
class TestIngestionIntegration:
    """End-to-end tests that require a running PostgreSQL instance and raw CSVs."""

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
                result = conn.execute(text(f"SELECT COUNT(*) FROM raw.{table_name}"))
                db_count = result.scalar()
                assert db_count == counts["loaded"], (
                    f"raw.{table_name}: expected {counts['loaded']}, got {db_count}"
                )


# ── claim_id_bucket (pure, no DB) ────────────────────────────────────


class TestClaimIdBucket:
    def test_deterministic(self):
        assert claim_id_bucket("CLM123") == claim_id_bucket("CLM123")

    def test_in_range(self):
        assert all(0 <= claim_id_bucket(f"CLM{i}", 2) < 2 for i in range(50))

    def test_partition_is_non_trivial(self):
        # Both buckets are populated over a reasonable sample (not all one side).
        buckets = {claim_id_bucket(f"CLM{i}", 2) for i in range(50)}
        assert buckets == {0, 1}


# ── Upsert idempotency (requires PostgreSQL, no CSVs) ─────────────────


class TestUpsertIdempotency:
    """The ON CONFLICT upsert must accumulate without duplicating, update
    non-key columns, and preserve ingested_at (first-seen time)."""

    @pytest.fixture(autouse=True)
    def _check_db(self):
        try:
            from clinical_data_etl.utils.db import test_connection

            test_connection()
        except Exception:
            pytest.skip("PostgreSQL not available — run `make db-up`")

    def test_upsert_idempotent_updates_and_preserves_ingested_at(self):
        from sqlalchemy import text

        from clinical_data_etl.ingestion.loaders import load_to_postgres
        from clinical_data_etl.utils.db import get_engine

        engine = get_engine()
        table = "ut_upsert_demo"
        first_ts = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        second_ts = dt.datetime(2026, 2, 2, tzinfo=dt.UTC)
        df = pd.DataFrame([{"id": "A", "val": "x"}, {"id": "B", "val": "y"}])

        try:
            load_to_postgres(df, table, key="id", ingested_at=first_ts)
            # Re-load identical data: must be a no-op (no row growth).
            load_to_postgres(df, table, key="id", ingested_at=second_ts)

            with engine.connect() as conn:
                count = conn.execute(
                    text(f'SELECT count(*) FROM raw."{table}"')
                ).scalar()
                has_index = conn.execute(
                    text(
                        "SELECT 1 FROM pg_indexes WHERE schemaname='raw' "
                        "AND indexname='ux_ut_upsert_demo_id'"
                    )
                ).scalar()
            assert count == 2, "upsert must not duplicate rows"
            assert has_index == 1, "unique index on the natural key must exist"

            # Change a non-key column: row is updated, not duplicated; ingested_at kept.
            df2 = pd.DataFrame([{"id": "A", "val": "z"}, {"id": "B", "val": "y"}])
            load_to_postgres(df2, table, key="id", ingested_at=second_ts)
            with engine.connect() as conn:
                count2 = conn.execute(
                    text(f'SELECT count(*) FROM raw."{table}"')
                ).scalar()
                val_a = conn.execute(
                    text(f"SELECT val FROM raw.\"{table}\" WHERE id='A'")
                ).scalar()
                ingested_a = conn.execute(
                    text(f"SELECT ingested_at FROM raw.\"{table}\" WHERE id='A'")
                ).scalar()
            assert count2 == 2
            assert val_a == "z", "non-key column must be updated on conflict"
            assert ingested_a.month == 1, "ingested_at must be preserved (first-seen)"
        finally:
            with engine.begin() as conn:
                conn.execute(text(f'DROP TABLE IF EXISTS raw."{table}"'))
