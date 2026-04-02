# Clinical Data ETL Pipeline

## Project Overview

A portfolio project demonstrating Data Engineering and Analytics Engineering skills through a multi-source clinical data ETL pipeline. The pipeline ingests real Kaggle healthcare datasets — primarily Medicare claims fraud detection data (4 related CSV tables) — validates each table with pandera, stages into PostgreSQL, transforms with dbt, and orchestrates the workflow with Prefect.

This project exists to showcase:
- Multi-source, multi-table ETL pipeline design and implementation
- Data quality validation with per-table pandera schemas
- Dimensional modeling and analytics engineering with dbt
- Workflow orchestration and error handling
- Infrastructure-as-code with Docker

### Data Sources

**PRIMARY — Medicare Claims Fraud Detection**
Source: Kaggle `rohitrox/healthcare-provider-fraud-detection-analysis`
Location: `data/raw/claims_fraud/`

| File | Description |
|------|-------------|
| `Train_Beneficiarydata-1542865627584.csv` | Beneficiary demographics: BeneID, DOB, DOD, Gender, Race, chronic condition flags, reimbursement amounts |
| `Test_Beneficiarydata-1542969243754.csv` | Beneficiary test split |
| `Train_Inpatientdata-1542865627584.csv` | Inpatient claims: BeneID, ClaimID, Provider, diagnosis/procedure codes, admission/discharge dates, reimbursement |
| `Test_Inpatientdata-1542969243754.csv` | Inpatient claims test split |
| `Train_Outpatientdata-1542865627584.csv` | Outpatient claims: same structure as inpatient, no admission dates |
| `Test_Outpatientdata-1542969243754.csv` | Outpatient claims test split |
| `Train-1542865627584.csv` | Provider fraud labels (Provider ID + PotentialFraud indicator) — train split |
| `Test-1542969243754.csv` | Provider fraud labels — test split |

**SECONDARY — Diabetes Readmission**
Source: Kaggle `brandao/diabetes`
Location: `data/raw/diabetes_readmission/`
- `diabetic_data.csv` — 70K+ inpatient encounters, 55 features, readmission outcome

**TERTIARY — Synthetic Hospital**
Source: Kaggle `amulyas/synth-hospital-data`
Location: `data/raw/synthetic_hospital/`
- `HospitalSynthetic1.csv` — Lightweight dataset for testing and development

## Tech Stack

| Tool         | Purpose                  | Version       |
|-------------|--------------------------|---------------|
| Python       | Core language            | 3.11+         |
| pandas       | Data manipulation        | 2.x           |
| pandera      | Schema validation        | 0.18+         |
| PostgreSQL   | Data warehouse           | 16 (Docker)   |
| dbt-core     | Transformation layer     | 1.7+          |
| dbt-postgres | dbt adapter              | 1.7+          |
| Prefect      | Orchestration            | 2.x           |
| Docker       | PostgreSQL hosting       | -             |
| pytest       | Testing                  | 8.x           |

## Architecture

```
CSV files (4 claims_fraud tables + diabetes + synthetic)
  │
  ▼
Ingestion (pandas + per-table pandera schemas)
  │  Beneficiary CSV ──→ pandera BeneficiarySchema
  │  Inpatient CSV   ──→ pandera InpatientClaimSchema
  │  Outpatient CSV  ──→ pandera OutpatientClaimSchema
  │  Provider CSV    ──→ pandera ProviderSchema
  │
  ▼
PostgreSQL raw schema
  │  raw.beneficiary
  │  raw.inpatient_claims
  │  raw.outpatient_claims
  │  raw.providers
  │
  ▼
dbt Transforms
  ├── staging   (stg_beneficiary, stg_inpatient_claims,
  │              stg_outpatient_claims, stg_providers)
  ├── intermediate (int_claims_joined, int_beneficiary_enriched)
  └── marts     (fct_claims, dim_beneficiary, dim_provider)
  │
  ▼
Orchestration (Prefect flows)
```

### Data Flow

1. **Ingestion**: Python reads CSVs from `data/raw/claims_fraud/` (and secondary datasets), validates each table against its pandera schema, loads into PostgreSQL `raw` schema as separate tables.
2. **Staging**: dbt staging models (`stg_beneficiary`, `stg_inpatient_claims`, `stg_outpatient_claims`, `stg_providers`) clean column names, cast types, merge train/test splits, and apply schema tests (not_null, unique, accepted_values).
3. **Intermediate**: dbt intermediate models join claims to beneficiaries and providers, compute derived fields (claim duration, age at claim, chronic condition counts).
4. **Marts**: dbt mart models produce analytics-ready tables — `fct_claims` (grain: one row per claim with all dimensions), `dim_beneficiary`, `dim_provider` (with fraud label).
5. **Orchestration**: Prefect flows coordinate the full pipeline: ingest → dbt run → dbt test, with retries and notifications.

## Folder Structure

```
clinical-data-etl/
├── CLAUDE.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── data/
│   └── raw/
│       ├── claims_fraud/           # Medicare claims fraud CSVs (primary)
│       ├── diabetes_readmission/   # Diabetes readmission CSV (secondary)
│       └── synthetic_hospital/     # Synthetic hospital CSV (tertiary)
├── src/
│   └── clinical_data_etl/
│       ├── __init__.py
│       ├── ingestion/      # CSV loading, pandera schemas, DB writes
│       │   ├── __init__.py
│       │   ├── loaders.py
│       │   └── schemas.py
│       ├── orchestration/  # Prefect flows and tasks
│       │   ├── __init__.py
│       │   └── flows.py
│       └── utils/          # DB connections, config, shared helpers
│           ├── __init__.py
│           └── db.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── seeds/
│   ├── macros/
│   └── tests/
└── tests/                  # pytest tests for Python code
    ├── conftest.py
    ├── test_ingestion/
    └── test_utils/
```

## Conventions

### Naming

- **Python**: snake_case for modules, functions, variables. Classes use PascalCase.
- **SQL / dbt models**: snake_case. Prefix staging models with `stg_`, intermediate with `int_`, marts with `fct_` (facts) or `dim_` (dimensions).
- **Database schemas**: `raw` (ingested data), `staging`, `intermediate`, `marts`.

### Testing

- **Python tests**: pytest in `tests/`. Unit test pandera schemas and ingestion logic. Use fixtures for sample DataFrames.
- **dbt tests**: Schema tests (not_null, unique, relationships, accepted_values) in YAML. Custom data tests in `dbt/tests/`.
- **Validation**: pandera schemas enforce types, nullability, and value ranges at ingestion time — fail fast on bad data.

### Commit Style

- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Keep commits small and focused on a single change.

### Code Style

- Type hints on all function signatures.
- Use `pathlib.Path` for file paths, not string concatenation.
- Configuration via environment variables (loaded from `.env`), never hardcoded credentials.

## Current Priority

**Task 5 — Scaffold the repo**

- Finalize folder structure and skeleton files
- Set up `pyproject.toml` with dependencies
- Create `docker-compose.yml` for PostgreSQL
- Add `.env.example` with required environment variables
- Wire up a basic Prefect flow that runs end-to-end (even if steps are stubs)
