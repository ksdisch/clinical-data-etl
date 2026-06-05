.PHONY: setup download-data db-up db-down test lint pipeline pipeline-reset pipeline-ingest pipeline-dbt demo-incremental demo-scd2 dbt-compile dbt-docs

# Scope Prefect's local DB to this project so a shared ~/.prefect/prefect.db
# from another project can't break flow runs (see BACKLOG.md).
export PREFECT_HOME := $(CURDIR)/.prefect

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

download-data:
	kaggle datasets download -d rohitrox/healthcare-provider-fraud-detection-analysis -p data/raw/claims_fraud/ --unzip
	kaggle datasets download -d brandao/diabetes -p data/raw/diabetes_readmission/ --unzip
	kaggle datasets download -d amulyas/synthetic-hospital-data -p data/raw/synthetic_hospital/ --unzip

db-up:
	docker compose up -d

db-down:
	docker compose down

test:
	pytest

lint:
	ruff check src/ tests/

pipeline:
	.venv/bin/python -m clinical_data_etl

# Clean rebuild: TRUNCATE raw (snapshots survive) + full-refresh dbt.
pipeline-reset:
	.venv/bin/python -m clinical_data_etl --reset

pipeline-ingest:
	.venv/bin/python -m clinical_data_etl --ingest-only

pipeline-dbt:
	.venv/bin/python -m clinical_data_etl --dbt-only

# Self-verifying demos (seeded, deterministic) for the new capabilities.
demo-incremental:
	.venv/bin/python scripts/demo_incremental.py

demo-scd2:
	.venv/bin/python scripts/demo_scd2.py

dbt-compile:
	.venv/bin/dbt compile --profiles-dir dbt --project-dir dbt

dbt-docs:
	.venv/bin/dbt docs generate --profiles-dir dbt --project-dir dbt
	.venv/bin/dbt docs serve --profiles-dir dbt --project-dir dbt
