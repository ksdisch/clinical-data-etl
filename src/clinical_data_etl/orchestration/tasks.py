"""Prefect tasks for the clinical data ETL pipeline."""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from prefect import get_run_logger, task
from sqlalchemy import text

from clinical_data_etl.utils.db import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DBT_DIR = PROJECT_ROOT / "dbt"
DBT_PROFILES_DIR = DBT_DIR

_fallback_logger = logging.getLogger(__name__)


def _get_logger() -> logging.Logger | logging.LoggerAdapter[Any]:
    """Get Prefect run logger if in a flow/task context, else stdlib logger."""
    try:
        return get_run_logger()
    except Exception:
        return _fallback_logger


@task(name="ingest-claims-data")
def ingest_task(mode: str = "upsert") -> dict[str, dict[str, int]]:
    """Run the full claims_fraud ingestion pipeline.

    Args:
        mode: ``upsert`` (accumulate, default) or ``replace`` (TRUNCATE first).
    """
    logger = _get_logger()

    from clinical_data_etl.ingestion.loaders import run_ingestion

    logger.info("Starting ingestion of claims_fraud dataset (mode=%s)...", mode)
    summary = run_ingestion(mode=mode)

    for table_name, counts in summary.items():
        logger.info(
            "raw.%s: %d loaded, %d rejected",
            table_name,
            counts["loaded"],
            counts["rejected"],
        )

    total_loaded = sum(c["loaded"] for c in summary.values())
    logger.info("Ingestion complete: %d total rows loaded", total_loaded)
    return summary


def _run_dbt_command(args: list[str]) -> str:
    """Run a dbt CLI command and return stdout. Raises on failure."""
    # Use the dbt binary from the same venv as the running Python
    dbt_bin = Path(sys.executable).parent / "dbt"
    cmd = [
        str(dbt_bin),
        *args,
        "--profiles-dir",
        str(DBT_PROFILES_DIR),
        "--project-dir",
        str(DBT_DIR),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"dbt {args[0]} failed (exit {result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout


@task(name="dbt-seed", retries=2, retry_delay_seconds=10)
def dbt_seed_task() -> str:
    """Load dbt seeds (reference/lookup data, e.g. the admission_type_mapping
    backing dim_admission_type). Runs before dbt_run so seed-backed models can
    build. Idempotent — re-seeding replaces the small lookup tables."""
    logger = _get_logger()
    logger.info("Running dbt seed...")
    output = _run_dbt_command(["seed"])
    logger.info("dbt seed completed successfully")
    return output


@task(name="dbt-snapshot", retries=2, retry_delay_seconds=10)
def dbt_snapshot_task() -> str:
    """Run dbt snapshots (SCD2 fraud-label history). Runs before dbt_run so the
    snapshot relation exists for dim_provider_history to build from."""
    logger = _get_logger()
    logger.info("Running dbt snapshot...")
    output = _run_dbt_command(["snapshot"])
    logger.info("dbt snapshot completed successfully")
    return output


@task(name="dbt-run", retries=2, retry_delay_seconds=10)
def dbt_run_task(full_refresh: bool = False) -> str:
    """Run dbt models. ``full_refresh`` rebuilds incremental models from scratch."""
    logger = _get_logger()
    logger.info("Running dbt run%s...", " --full-refresh" if full_refresh else "")
    args = ["run", "--full-refresh"] if full_refresh else ["run"]
    output = _run_dbt_command(args)
    logger.info("dbt run completed successfully")
    return output


@task(name="dbt-test", retries=2, retry_delay_seconds=10)
def dbt_test_task() -> str:
    """Run dbt tests."""
    logger = _get_logger()
    logger.info("Running dbt test...")
    output = _run_dbt_command(["test"])
    logger.info("dbt test completed successfully")
    return output


@task(name="validate-marts")
def validate_marts_task() -> dict[str, int]:
    """Verify mart tables exist and have rows."""
    logger = _get_logger()
    logger.info("Validating mart tables...")

    engine = get_engine()
    mart_tables = [
        # Claims star
        "fct_claims",
        "dim_beneficiary",
        "dim_provider",
        "dim_provider_history",
        # Diabetes star
        "fct_encounters",
        "dim_patient",
        "dim_admission_type",
        # Hospital star
        "fct_hospital_admissions",
        "dim_hospital_patient",
        "dim_severity",
    ]
    row_counts: dict[str, int] = {}

    with engine.connect() as conn:
        for table in mart_tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM raw_marts.{table}"))
            count = result.scalar() or 0
            row_counts[table] = count
            logger.info("raw_marts.%s: %d rows", table, count)

            if count == 0:
                raise RuntimeError(f"Mart table raw_marts.{table} is empty!")

    logger.info("All mart tables validated successfully")
    return row_counts
