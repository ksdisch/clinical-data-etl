# Clinical Data ETL Pipeline

## Project Overview

A portfolio project demonstrating Data Engineering and Analytics Engineering skills through a clinical data ETL pipeline. The pipeline ingests synthetic NDNQI (National Database of Nursing Quality Indicators) falls data from CSV files in long format, validates and stages it in PostgreSQL, transforms it with dbt, and orchestrates the workflow with Prefect.

This project exists to showcase:
- End-to-end ETL pipeline design and implementation
- Data quality validation and testing practices
- Dimensional modeling and analytics engineering with dbt
- Workflow orchestration and error handling
- Infrastructure-as-code with Docker

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
CSV (long format)
  │
  ▼
Ingestion (pandas + pandera validation)
  │
  ▼
Staging (PostgreSQL raw schema)
  │
  ▼
dbt Transforms
  ├── staging models (cleaned, typed, tested)
  ├── intermediate models (pivoted, joined)
  └── marts (analytics-ready tables)
  │
  ▼
Orchestration (Prefect flows)
```

### Data Flow

1. **Ingestion**: Python reads CSV files from `data/synthetic/`, validates with pandera schemas, loads raw data into PostgreSQL `raw` schema.
2. **Staging**: dbt staging models clean column names, cast types, deduplicate, and apply basic tests (not_null, unique, accepted_values).
3. **Intermediate**: dbt intermediate models pivot long-format data to wide, join reference tables, compute derived fields.
4. **Marts**: dbt mart models produce analytics-ready tables (e.g., fall rates by unit, risk-adjusted metrics).
5. **Orchestration**: Prefect flows coordinate the full pipeline: ingest → dbt run → dbt test, with retries and notifications.

## Folder Structure

```
clinical-data-etl/
├── CLAUDE.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── data/
│   └── synthetic/          # Synthetic NDNQI falls CSVs
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

**Task 7 — Build ingestion layer (pandera validation → PostgreSQL staging)**

- Define pandera schemas in `src/clinical_data_etl/ingestion/schemas.py` for falls CSV columns
- Implement CSV loader in `loaders.py`: read CSV, validate with pandera, write to PostgreSQL `raw` schema
- Add database connection helper in `utils/db.py` using SQLAlchemy + python-dotenv
- Write pytest tests for schema validation (valid data passes, bad data fails)
- Test end-to-end: CSV → validate → PostgreSQL `raw.falls` table
