# Clinical Data ETL Pipeline

An end-to-end ETL pipeline for clinical falls data, built with Python, PostgreSQL, dbt, and Prefect.

## Architecture

```
  CSV files (NDNQI falls data, long format)
       │
       ▼
  ┌─────────────────────────┐
  │  Ingestion (Python)     │
  │  pandas + pandera       │
  │  schema validation      │
  └────────┬────────────────┘
           ▼
  ┌─────────────────────────┐
  │  PostgreSQL (raw)       │
  │  Staging tables         │
  └────────┬────────────────┘
           ▼
  ┌─────────────────────────┐
  │  dbt Transforms         │
  │  staging → intermediate │
  │  → marts                │
  └────────┬────────────────┘
           ▼
  ┌─────────────────────────┐
  │  Analytics-ready tables │
  │  (fact + dimension)     │
  └─────────────────────────┘

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
data/synthetic/           Sample NDNQI falls data
```

## Tech Stack

- **Python** (pandas, pandera) — ingestion and validation
- **PostgreSQL 16** — data warehouse (via Docker)
- **dbt** — SQL transformations and testing
- **Prefect** — workflow orchestration
