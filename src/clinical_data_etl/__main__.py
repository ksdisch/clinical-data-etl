"""CLI entry point: python -m clinical_data_etl"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clinical Data ETL Pipeline",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--ingest-only",
        action="store_true",
        help="Run only the ingestion step",
    )
    group.add_argument(
        "--dbt-only",
        action="store_true",
        help="Run only dbt run + test (skip ingestion)",
    )
    group.add_argument(
        "--full",
        action="store_true",
        default=True,
        help="Run full pipeline (default)",
    )

    args = parser.parse_args()

    from clinical_data_etl.orchestration.flows import pipeline_flow

    if args.ingest_only:
        pipeline_flow(run_ingestion=True, run_dbt=False)
    elif args.dbt_only:
        pipeline_flow(run_ingestion=False, run_dbt=True)
    else:
        pipeline_flow(run_ingestion=True, run_dbt=True)


if __name__ == "__main__":
    main()
