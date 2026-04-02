# Clinical Data ETL Pipeline

A multi-source clinical data ETL pipeline built with Python, PostgreSQL, dbt, and Prefect. Primary dataset: Medicare Claims Fraud Detection (4 related CSV tables from Kaggle).

## Architecture

```
  CSV files (Medicare claims, diabetes readmission, synthetic)
       │
       ▼
  ┌──────────────────────────────┐
  │  Ingestion (Python)          │
  │  pandas + pandera            │
  │  per-table schema validation │
  └────────┬─────────────────────┘
           ▼
  ┌──────────────────────────────┐
  │  PostgreSQL (raw schema)     │
  │  raw.beneficiary             │
  │  raw.inpatient_claims        │
  │  raw.outpatient_claims       │
  │  raw.providers               │
  └────────┬─────────────────────┘
           ▼
  ┌──────────────────────────────┐
  │  dbt Transforms              │
  │  staging → intermediate      │
  │  → marts (fct/dim)           │
  └────────┬─────────────────────┘
           ▼
  ┌──────────────────────────────┐
  │  fct_claims                  │
  │  dim_beneficiary             │
  │  dim_provider                │
  └──────────────────────────────┘

  Orchestrated by Prefect
```

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/clinical-data-etl.git
cd clinical-data-etl
```

### 2. Start PostgreSQL

```bash
cp .env.example .env
docker compose up -d
```

### 3. Create a virtual environment and install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 4. Verify dbt connection

```bash
cd dbt
dbt debug
cd ..
```

### 5. Run the pipeline

```bash
# Coming soon — Prefect flow orchestration
```

## Project Structure

```
src/clinical_data_etl/    Python package (ingestion, orchestration, utils)
dbt/                      dbt project (staging, intermediate, marts models)
tests/                    pytest test suite
data/raw/                 Kaggle datasets (not committed — see CLAUDE.md for sources)
```

## Tech Stack

- **Python** (pandas, pandera) — ingestion and validation
- **PostgreSQL 16** — data warehouse (via Docker)
- **dbt** — SQL transformations and testing
- **Prefect** — workflow orchestration
