"""Prefect flows for pipeline orchestration."""

import time
from typing import Any

from prefect import flow, get_run_logger

from clinical_data_etl.orchestration.tasks import (
    dbt_run_task,
    dbt_test_task,
    ingest_task,
    validate_marts_task,
)


@flow(name="clinical-data-etl-pipeline")
def pipeline_flow(
    run_ingestion: bool = True,
    run_dbt: bool = True,
) -> dict[str, Any]:
    """End-to-end clinical data ETL pipeline.

    Args:
        run_ingestion: Whether to run the ingestion step.
        run_dbt: Whether to run the dbt run/test steps.
    """
    logger = get_run_logger()
    start = time.time()
    summary: dict[str, Any] = {}

    if run_ingestion:
        logger.info("Step 1/4: Ingesting claims data...")
        summary["ingestion"] = ingest_task()
    else:
        logger.info("Step 1/4: Skipping ingestion")

    if run_dbt:
        logger.info("Step 2/4: Running dbt models...")
        summary["dbt_run"] = dbt_run_task()

        logger.info("Step 3/4: Running dbt tests...")
        summary["dbt_test"] = dbt_test_task()
    else:
        logger.info("Steps 2-3/4: Skipping dbt")

    logger.info("Step 4/4: Validating mart tables...")
    summary["mart_row_counts"] = validate_marts_task()

    elapsed = time.time() - start
    logger.info("Pipeline completed in %.1f seconds", elapsed)

    return summary
