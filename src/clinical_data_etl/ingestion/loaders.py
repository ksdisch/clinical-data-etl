"""CSV loading, validation, and PostgreSQL staging for claims_fraud dataset."""

import datetime as dt
import hashlib
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera.pandas import DataFrameSchema
from sqlalchemy import text
from sqlalchemy.engine import Connection

from clinical_data_etl.ingestion.schemas import (
    BeneficiarySchema,
    DiabetesEncounterSchema,
    InpatientClaimSchema,
    OutpatientClaimSchema,
    ProviderSchema,
)
from clinical_data_etl.utils.db import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "claims_fraud"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected"

# --- Secondary source: diabetes readmission (single CSV, no train/test split) ---
DIABETES_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "diabetes_readmission"
DIABETES_CSV_GLOB = "diabetic_data.csv"
DIABETES_TABLE = "diabetes_encounters"
DIABETES_MISSING_SENTINEL = "?"

# Natural key per logical table — the column (as named in the merged DataFrame)
# that uniquely identifies a row and backs the idempotent ON CONFLICT upsert.
NATURAL_KEYS: dict[str, str] = {
    "beneficiary": "BeneID",
    "inpatient_claims": "ClaimID",
    "outpatient_claims": "ClaimID",
    "providers": "Provider",
    DIABETES_TABLE: "encounter_id",
}

# Audit column stamped on every loaded row. It records FIRST-seen time and is
# deliberately NOT overwritten on re-ingest, so an unchanged re-load is a no-op.
INGESTED_AT_COL = "ingested_at"

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


def clean_diabetes_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Recode the diabetes dataset's '?' missing sentinel to NA.

    The UCI diabetes CSV encodes missing categorical values as the literal
    string ``?`` (e.g. race, weight, payer_code, medical_specialty, diag_*).
    pandera's ``nullable`` checks only recognise NA/NaN, so this must run
    BEFORE validation. Returns a copy — pure and DB-free, so it is unit-testable.
    """
    return df.replace(DIABETES_MISSING_SENTINEL, pd.NA)


def load_diabetes() -> pd.DataFrame:
    """Read the single diabetes-encounters CSV and recode missing sentinels.

    Unlike the claims tables there is no Train/Test split to merge — one CSV,
    one row per hospital encounter.
    """
    files = sorted(DIABETES_DATA_DIR.glob(DIABETES_CSV_GLOB))
    if not files:
        raise FileNotFoundError(
            f"No diabetes CSV matching {DIABETES_CSV_GLOB} in {DIABETES_DATA_DIR}"
        )
    raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    return clean_diabetes_frame(raw)


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


def claim_id_bucket(claim_id: str, n_buckets: int = 2) -> int:
    """Deterministic, stable bucket for a claim_id (used by the incremental demo).

    Uses md5 (not Python's salted hash) so the partition is reproducible across
    processes and runs.
    """
    digest = hashlib.md5(str(claim_id).encode()).hexdigest()
    return int(digest, 16) % n_buckets


def _ensure_table_and_index(
    conn: Connection,
    frame: pd.DataFrame,
    table_name: str,
    schema: str,
    key: str,
) -> None:
    """Create the target table (from the frame's shape) if absent and ensure a
    UNIQUE index on the natural key so ON CONFLICT has something to conflict on.
    """
    exists = conn.execute(
        text("select to_regclass(:rel)"),
        {"rel": f"{schema}.{table_name}"},
    ).scalar()
    if exists is None:
        frame.head(0).to_sql(
            table_name, conn, schema=schema, if_exists="append", index=False
        )
    conn.execute(
        text(
            f'CREATE UNIQUE INDEX IF NOT EXISTS "ux_{table_name}_{key.lower()}" '
            f'ON {schema}."{table_name}" ("{key}")'
        )
    )


def load_to_postgres(
    df: pd.DataFrame,
    table_name: str,
    schema: str = "raw",
    *,
    mode: str = "upsert",
    key: str | None = None,
    ingested_at: dt.datetime | None = None,
) -> int:
    """Idempotently load a DataFrame into PostgreSQL via ON CONFLICT upsert.

    The raw tables ACCUMULATE across runs (no DROP CASCADE): rows are inserted
    into a session staging table, then `INSERT ... ON CONFLICT (key) DO UPDATE`
    merges them into the target keyed on the natural key. ``ingested_at`` is
    stamped once and never overwritten, so re-loading identical data is a no-op.

    Args:
        df: validated rows to load.
        table_name: logical/raw table name.
        schema: target schema (default ``raw``).
        mode: ``upsert`` (accumulate, default) or ``replace`` (TRUNCATE first —
            preserves dependent dbt views and DB-resident snapshots, unlike the
            old DROP ... CASCADE).
        key: natural key column; defaults to ``NATURAL_KEYS[table_name]``.
        ingested_at: batch timestamp; defaults to ``now(UTC)``. Passing a fixed
            value makes the load byte-reproducible.

    Returns:
        Number of rows processed (``len(df)``).
    """
    if key is None:
        key = NATURAL_KEYS[table_name]
    if ingested_at is None:
        ingested_at = dt.datetime.now(dt.UTC)

    frame = df.copy()
    frame[INGESTED_AT_COL] = ingested_at

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        _ensure_table_and_index(conn, frame, table_name, schema, key)

        if mode == "replace":
            conn.execute(text(f'TRUNCATE TABLE {schema}."{table_name}"'))
        elif mode != "upsert":
            raise ValueError(f"Unknown load mode: {mode!r} (use 'upsert' or 'replace')")

        staging_table = f"_stage_{table_name}"
        frame.to_sql(
            staging_table, conn, schema=schema, if_exists="replace", index=False
        )

        columns = list(frame.columns)
        col_list = ", ".join(f'"{c}"' for c in columns)
        # ingested_at is excluded from the update so first-seen time is preserved.
        update_cols = [c for c in columns if c not in (key, INGESTED_AT_COL)]
        if update_cols:
            set_clause = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)
            conflict = f'ON CONFLICT ("{key}") DO UPDATE SET {set_clause}'
        else:
            conflict = f'ON CONFLICT ("{key}") DO NOTHING'

        conn.execute(
            text(
                f'INSERT INTO {schema}."{table_name}" ({col_list}) '
                f'SELECT {col_list} FROM {schema}."{staging_table}" '
                f"{conflict}"
            )
        )
        conn.execute(text(f'DROP TABLE {schema}."{staging_table}"'))

    return len(frame)


def reset_raw_tables(schema: str = "raw") -> None:
    """TRUNCATE all raw claims tables for a clean rebuild without dropping the
    tables (so dependent dbt views) or the DB-resident snapshots.
    """
    engine = get_engine()
    with engine.begin() as conn:
        for table_name in (*TABLE_CONFIG, DIABETES_TABLE):
            exists = conn.execute(
                text("select to_regclass(:rel)"),
                {"rel": f"{schema}.{table_name}"},
            ).scalar()
            if exists is not None:
                conn.execute(text(f'TRUNCATE TABLE {schema}."{table_name}"'))


def run_ingestion(
    mode: str = "upsert",
    ingested_at: dt.datetime | None = None,
) -> dict[str, dict[str, int]]:
    """Run full ingestion pipeline across both sources.

    Primary source: the 4 claims_fraud tables (Train/Test CSVs merged).
    Secondary source: the diabetes_readmission encounters (single CSV).

    Args:
        mode: ``upsert`` (accumulate, default) or ``replace`` (TRUNCATE first).
        ingested_at: shared batch timestamp for all tables; defaults to now(UTC).

    Returns summary dict: {table_name: {"loaded": N, "rejected": N}}
    """
    summary: dict[str, dict[str, int]] = {}
    if ingested_at is None:
        ingested_at = dt.datetime.now(dt.UTC)

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
        loaded = load_to_postgres(
            valid_df, table_name, mode=mode, ingested_at=ingested_at
        )
        print(f"  Loaded: {loaded} rows to raw.{table_name}")

        summary[table_name] = {
            "loaded": loaded,
            "rejected": len(rejected_df),
        }

    # --- Secondary source: diabetes readmission (single CSV, no train/test) ---
    print(f"\n{'=' * 50}")
    print(f"Processing: {DIABETES_TABLE}")
    print(f"{'=' * 50}")

    print("  Loading diabetes encounters CSV (recoding '?' -> NA)...")
    diabetes_df = load_diabetes()
    print(f"  Loaded: {len(diabetes_df)} rows")

    print("  Validating against schema...")
    valid_df, rejected_df = validate(
        diabetes_df, DiabetesEncounterSchema, DIABETES_TABLE
    )
    print(f"  Valid: {len(valid_df)} rows")

    print("  Loading to PostgreSQL raw schema...")
    loaded = load_to_postgres(
        valid_df, DIABETES_TABLE, mode=mode, ingested_at=ingested_at
    )
    print(f"  Loaded: {loaded} rows to raw.{DIABETES_TABLE}")

    summary[DIABETES_TABLE] = {
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
