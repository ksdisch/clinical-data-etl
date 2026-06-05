"""Prefect flows for pipeline orchestration."""

import time
from typing import Any

from prefect import flow, get_run_logger

from clinical_data_etl.orchestration.tasks import (
    dbt_run_task,
    dbt_seed_task,
    dbt_snapshot_task,
    dbt_test_task,
    ingest_task,
    validate_marts_task,
)


@flow(name="clinical-data-etl-pipeline")
def pipeline_flow(
    run_ingestion: bool = True,
    run_dbt: bool = True,
    reset: bool = False,
) -> dict[str, Any]:
    """End-to-end clinical data ETL pipeline.

    Args:
        run_ingestion: Whether to run the ingestion step.
        run_dbt: Whether to run the dbt snapshot/run/test steps.
        reset: Clean rebuild — TRUNCATE raw (snapshots survive) and full-refresh
            incremental dbt models. Default is incremental/idempotent accumulation.
    """
    logger = get_run_logger()
    start = time.time()
    summary: dict[str, Any] = {}

    if run_ingestion:
        mode = "replace" if reset else "upsert"
        logger.info("Step 1/6: Ingesting both sources (mode=%s)...", mode)
        summary["ingestion"] = ingest_task(mode=mode)
    else:
        logger.info("Step 1/6: Skipping ingestion")

    if run_dbt:
        logger.info("Step 2/6: Loading dbt seeds (lookup dimensions)...")
        summary["dbt_seed"] = dbt_seed_task()

        logger.info("Step 3/6: Building SCD2 snapshots...")
        summary["dbt_snapshot"] = dbt_snapshot_task()

        logger.info(
            "Step 4/6: Running dbt models%s...", " (full-refresh)" if reset else ""
        )
        summary["dbt_run"] = dbt_run_task(full_refresh=reset)

        logger.info("Step 5/6: Running dbt tests...")
        summary["dbt_test"] = dbt_test_task()
    else:
        logger.info("Steps 2-5/6: Skipping dbt")

    logger.info("Step 6/6: Validating mart tables...")
    summary["mart_row_counts"] = validate_marts_task()

    elapsed = time.time() - start
    logger.info("Pipeline completed in %.1f seconds", elapsed)

    return summary
