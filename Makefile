.PHONY: setup download-data db-up db-down test lint pipeline

setup:
	python3.12 -m venv .venv
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
	@echo "TODO: Run full ETL pipeline (Prefect flow)"
