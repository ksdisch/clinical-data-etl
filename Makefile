.PHONY: setup download-data db-up db-down test lint pipeline pipeline-ingest pipeline-dbt

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

pipeline-ingest:
	.venv/bin/python -m clinical_data_etl --ingest-only

pipeline-dbt:
	.venv/bin/python -m clinical_data_etl --dbt-only
