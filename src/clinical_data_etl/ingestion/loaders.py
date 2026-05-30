"""CSV loading, validation, and PostgreSQL staging for claims_fraud dataset."""

from pathlib import Path

import pandas as pd
import pandera as pa
from pandera.pandas import DataFrameSchema
from sqlalchemy import text

from clinical_data_etl.ingestion.schemas import (
    BeneficiarySchema,
    InpatientClaimSchema,
    OutpatientClaimSchema,
    ProviderSchema,
)
from clinical_data_etl.utils.db import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "claims_fraud"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected"

# Mapping from logical table name to (Train glob, Test glob, schema)
TABLE_CONFIG: dict[str, tuple[str, str, DataFrameSchema]] = {
    "beneficiary": (
        "Train_Beneficiarydata-*.csv",
        "Test_Beneficiarydata-*.csv",
        BeneficiarySchema,
    ),
    "inpatient_claims": (
        "Train_Inpatientdata-*.csv",
        "Test_Inpatientdata-*.csv",
        InpatientClaimSchema,
    ),
    "outpatient_claims": (
        "Train_Outpatientdata-*.csv",
        "Test_Outpatientdata-*.csv",
        OutpatientClaimSchema,
    ),
    "providers": (
        "Train-*.csv",
        "Test-*.csv",
        ProviderSchema,
    ),
}


def load_and_merge(table_name: str) -> pd.DataFrame:
    """Read Train + Test CSVs for a table, concatenate, and return merged DataFrame.

    For the providers table, the Test split has no PotentialFraud column —
    this is handled by adding it as NaN before concatenation.
    """
    train_glob, test_glob, _ = TABLE_CONFIG[table_name]

    train_files = sorted(DATA_DIR.glob(train_glob))
    test_files = sorted(DATA_DIR.glob(test_glob))

    if not train_files:
        raise FileNotFoundError(f"No train files matching {train_glob} in {DATA_DIR}")
    if not test_files:
        raise FileNotFoundError(f"No test files matching {test_glob} in {DATA_DIR}")

    train_df = pd.concat([pd.read_csv(f) for f in train_files], ignore_index=True)
    test_df = pd.concat([pd.read_csv(f) for f in test_files], ignore_index=True)

    # Handle missing PotentialFraud column in Test provider split
    for col in train_df.columns:
        if col not in test_df.columns:
            test_df[col] = pd.NA

    merged = pd.concat([train_df, test_df], ignore_index=True)

    # Deduplicate: beneficiaries/providers appear in both Train and Test splits.
    # Keep first occurrence (Train row preferred over Test).
    dedup_keys = {
        "beneficiary": "BeneID",
        "providers": "Provider",
    }
    if table_name in dedup_keys:
        key = dedup_keys[table_name]
        before = len(merged)
        merged = merged.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
        dupes = before - len(merged)
        if dupes:
            print(f"  Deduplicated: removed {dupes} duplicate {key}s")

    return merged


def validate(
    df: pd.DataFrame,
    schema: DataFrameSchema,
    table_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate DataFrame against a pandera schema.

    Returns (valid_rows, rejected_rows). Rejected rows are saved to
    data/rejected/{table_name}_rejected.csv.
    """
    try:
        valid = schema.validate(df, lazy=True)
        return valid, pd.DataFrame()
    except pa.errors.SchemaErrors as exc:
        failure_indices = exc.failure_cases["index"].dropna().unique()
        rejected_mask = df.index.isin(failure_indices)
        rejected = df[rejected_mask].copy()
        valid = df[~rejected_mask].copy()

        # Re-validate the valid subset (coerce types)
        try:
            valid = schema.validate(valid, lazy=True)
        except pa.errors.SchemaErrors:
            # If column-level errors remain after row removal, raise
            raise

        # Save rejected rows
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        rejected_path = REJECTED_DIR / f"{table_name}_rejected.csv"
        rejected.to_csv(rejected_path, index=False)
        print(f"  {len(rejected)} rejected rows saved to {rejected_path}")

        return valid, rejected


def load_to_postgres(
    df: pd.DataFrame,
    table_name: str,
    schema: str = "raw",
) -> int:
    """Load DataFrame to PostgreSQL. Creates schema if needed. Returns row count."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        # CASCADE drops dependent views (dbt staging views)
        # which get recreated by dbt run
        conn.execute(text(f"DROP TABLE IF EXISTS {schema}.{table_name} CASCADE"))
        conn.commit()

    df.to_sql(
        table_name,
        engine,
        schema=schema,
        if_exists="append",
        index=False,
    )
    return len(df)


def run_ingestion() -> dict[str, dict[str, int]]:
    """Run full ingestion pipeline for all 4 claims_fraud tables.

    Returns summary dict: {table_name: {"loaded": N, "rejected": N}}
    """
    summary: dict[str, dict[str, int]] = {}

    for table_name, (_, _, schema) in TABLE_CONFIG.items():
        print(f"\n{'=' * 50}")
        print(f"Processing: {table_name}")
        print(f"{'=' * 50}")

        print("  Loading and merging Train/Test CSVs...")
        df = load_and_merge(table_name)
        print(f"  Merged: {len(df)} rows")

        print("  Validating against schema...")
        valid_df, rejected_df = validate(df, schema, table_name)
        print(f"  Valid: {len(valid_df)} rows")

        print("  Loading to PostgreSQL raw schema...")
        loaded = load_to_postgres(valid_df, table_name)
        print(f"  Loaded: {loaded} rows to raw.{table_name}")

        summary[table_name] = {
            "loaded": loaded,
            "rejected": len(rejected_df),
        }

    print(f"\n{'=' * 50}")
    print("Ingestion complete!")
    for table_name, counts in summary.items():
        loaded, rejected = counts["loaded"], counts["rejected"]
        print(f"  raw.{table_name}: {loaded} loaded, {rejected} rejected")

    return summary


if __name__ == "__main__":
    run_ingestion()
