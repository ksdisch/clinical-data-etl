# Clinical Data ETL Pipeline — Project Guide

> A multi-source clinical-data ETL pipeline I built to demonstrate Data Engineering and Analytics Engineering skills end-to-end: validated ingestion → PostgreSQL warehouse → dbt star-schema marts → Prefect orchestration, all wired up with CI.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![dbt](https://img.shields.io/badge/dbt-1.7-orange)
![Postgres](https://img.shields.io/badge/postgres-16-336791)
![Prefect](https://img.shields.io/badge/prefect-2.x-024dfd)
![CI](https://github.com/ksdisch/clinical-data-etl/actions/workflows/ci.yml/badge.svg)

---

## Table of Contents

- [TL;DR](#tldr)
- [What This Project Is](#what-this-project-is)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Key Flows](#key-flows)
  - [Flow 1: End-to-End Pipeline (`make pipeline`)](#flow-1-end-to-end-pipeline-make-pipeline)
  - [Flow 2: Ingesting One Table (Providers)](#flow-2-ingesting-one-table-providers)
  - [Flow 3: Raw → Staging → Intermediate → Marts](#flow-3-raw--staging--intermediate--marts)
  - [Flow 4: Failure Handling — Rejected Rows and dbt Retries](#flow-4-failure-handling--rejected-rows-and-dbt-retries)
- [Project History](#project-history)
  - [Milestone Summary](#milestone-summary)
  - [Decisions & Tradeoffs](#decisions--tradeoffs)
  - [Full Chronology](#full-chronology)
- [Repository Structure](#repository-structure)
- [User Guide](#user-guide)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running Locally](#running-locally)
  - [Usage Examples](#usage-examples)
  - [Common Workflows](#common-workflows)
  - [Troubleshooting](#troubleshooting)
- [Footer](#footer)

---

## TL;DR

I built a small but production-shaped data pipeline that takes raw Medicare claims-fraud CSV files (eight of them, ~848K rows in total), checks every row against typed schemas, loads the survivors into PostgreSQL, and then transforms them into a clean star-schema warehouse with dbt — all wrapped in a single Prefect flow that runs end-to-end with `make pipeline` in about 36 seconds.

The most interesting thing about it is that it isn't a toy. Every stage has the things you'd expect in a real platform: per-table data contracts (pandera), rejected-row quarantine, idempotent loads, dimensional modelling, both schema-level and custom data tests, and CI that spins up a real Postgres service to run the integration tests against.

## What This Project Is

This is a portfolio repo. I built it to give recruiters and hiring managers something concrete to look at when I claim Data Engineering / Analytics Engineering skills — and to give myself a sandbox where I could exercise the full toolchain (pandas, pandera, dbt, Prefect, Postgres, Docker, CI) on a real, messy, multi-table dataset.

The pipeline ingests Kaggle's Medicare provider fraud-detection dataset, which is genuinely well-suited for this kind of demo:

- **Four related tables** (beneficiaries, inpatient claims, outpatient claims, providers) — enough surface area to model joins, dimensions, and a star schema.
- **A real data-quality wrinkle**: the dataset is split into Train/Test files, and the Test provider file has no fraud-label column. That mismatch forces an explicit decision instead of a happy-path glide.
- **A real domain story**: claims, beneficiaries, providers, fraud labels — material that's recognisable to anyone who has worked in healthcare analytics.

**Status:** MVP is complete and working end-to-end. The repo is portfolio-grade, not actively in production. Phase 2 ideas (the diabetes-readmission and synthetic-hospital datasets that are scaffolded but not wired up) are deliberately deferred.

## Tech Stack

| Component | Tool / Library | Why I Chose It |
|---|---|---|
| Language | Python 3.11+ (venv created with 3.12) | Lingua franca for data work; the rest of the stack assumes it. |
| DataFrame layer | pandas 2.x | Standard, well-understood, plays cleanly with both pandera and SQLAlchemy. |
| Schema validation | pandera 0.18+ | Lets me declare per-table schemas as code, validate lazily, and partition rows into valid + rejected sets. Cheaper than Great Expectations for a four-table project. |
| DB driver | SQLAlchemy 2.0 + psycopg2-binary | SQLAlchemy gives me a portable engine API; the binary psycopg2 wheel keeps the install simple. |
| Warehouse | PostgreSQL 16 (Dockerised) | Free, well-supported by dbt, behaves enough like a "real" warehouse for a portfolio demo without paying for Snowflake/BigQuery. |
| Transformations | dbt-core 1.7+ + dbt-postgres 1.7+ | The standard tool for analytics engineering; demonstrates staging/intermediate/marts layering, schema tests, custom data tests, and ref-graph dependency management. |
| Orchestration | Prefect 2.x | Lighter to develop locally than Airflow, supports `@flow`/`@task` with retries, and gives me a logger I can attach the whole pipeline to. |
| Quality / tests | pytest 8, ruff, mypy (strict) | Pytest for behaviour; ruff for fast lint + format; strict mypy on `src/` to keep the Python types honest. |
| Container | Docker Compose | One-command Postgres with a healthcheck and persistent volume. |
| CI | GitHub Actions | Three-job matrix: lint, typecheck, test (with a real Postgres service). |
| AI assistance | Claude Code GitHub workflows | `@claude` mentions for PR review and assist; opt-in, doesn't run unless invoked. |

## Architecture

```mermaid
flowchart TD
    subgraph Source["Raw CSVs (data/raw/claims_fraud/)"]
        B1[Train_Beneficiarydata.csv]
        B2[Test_Beneficiarydata.csv]
        I1[Train_Inpatientdata.csv]
        I2[Test_Inpatientdata.csv]
        O1[Train_Outpatientdata.csv]
        O2[Test_Outpatientdata.csv]
        P1[Train.csv – Provider+Fraud]
        P2[Test.csv – Provider only]
    end

    subgraph Ingest["Ingestion (Python)"]
        L[load_and_merge<br/>Train+Test → one DataFrame]
        V[validate<br/>per-table pandera schema]
        R[rejected rows →<br/>data/rejected/*.csv]
        W[load_to_postgres<br/>DROP CASCADE + to_sql]
    end

    subgraph PG["PostgreSQL 16 (Docker)"]
        RAW[(raw schema:<br/>beneficiary, inpatient_claims,<br/>outpatient_claims, providers)]
        STG[(staging views:<br/>stg_*)]
        INT[(intermediate views:<br/>int_claims_unified,<br/>int_claims_enriched)]
        MARTS[(marts tables:<br/>fct_claims,<br/>dim_beneficiary,<br/>dim_provider)]
    end

    subgraph DBT["dbt run + test"]
        D1[staging models]
        D2[intermediate models]
        D3[mart models]
        D4[28 schema + custom tests]
    end

    subgraph Prefect["Prefect flow"]
        F[pipeline_flow]
        T1[ingest_task]
        T2[dbt_run_task<br/>retries=2]
        T3[dbt_test_task<br/>retries=2]
        T4[validate_marts_task]
    end

    Source --> L --> V
    V --> R
    V --> W --> RAW
    RAW --> D1 --> STG
    STG --> D2 --> INT
    INT --> D3 --> MARTS
    D4 -.tests.-> STG
    D4 -.tests.-> INT
    D4 -.tests.-> MARTS

    F --> T1 --> T2 --> T3 --> T4
    T1 -.runs.-> Ingest
    T2 -.runs.-> DBT
    T4 -.queries.-> MARTS
```

The shape is conventional ELT for a reason: it's the shape that matches what most modern data teams use, which is the point of the demo. Raw CSVs land in `raw.*` tables more or less as-is (just type-coerced); dbt does the actual cleaning, joining, and modelling; Prefect coordinates the whole thing and gives me a single command to run.

## Key Flows

### Flow 1: End-to-End Pipeline (`make pipeline`)

This is the canonical "make it run" path. Walking it top to bottom:

1. **Entry point**: `make pipeline` calls `python -m clinical_data_etl` ([`Makefile:25-26`](Makefile)).
2. **CLI parsing**: `src/clinical_data_etl/__main__.py` parses `--ingest-only` / `--dbt-only` / `--full` and calls `pipeline_flow(...)` with the right booleans.
3. **Prefect flow boots**: `src/clinical_data_etl/orchestration/flows.py:16` — the `@flow(name="clinical-data-etl-pipeline")` opens a run logger and timer.
4. **Step 1/4 — ingest**: calls `ingest_task()` (which wraps `run_ingestion()` from `loaders.py`). For each of the four tables it prints/logs counts of merged, valid, and loaded rows.
5. **Step 2/4 — dbt run**: `dbt_run_task` shells out to the `dbt` binary in the same venv via `subprocess.run`, with `retries=2, retry_delay_seconds=10`. Materialises 4 staging views, 2 intermediate views, and 3 mart tables.
6. **Step 3/4 — dbt test**: `dbt_test_task` runs `dbt test`. 28 tests (schema + custom) execute against the warehouse.
7. **Step 4/4 — mart sanity check**: `validate_marts_task` opens a SQLAlchemy connection and `SELECT COUNT(*)`s each mart in `raw_marts.*`. Raises if any is empty — an empty mart almost always means an upstream failure that didn't bubble up.
8. **Wrap-up**: the flow logs `"Pipeline completed in %.1f seconds"` and returns a summary dict that includes ingestion counts, dbt stdout, and mart row counts.

End-to-end takes ~36 seconds on my machine for ~848K input rows.

### Flow 2: Ingesting One Table (Providers)

Providers is the most interesting table to trace because it surfaces the Train/Test column mismatch that drove a real design decision. Trace from `loaders.py`:

1. **`load_and_merge("providers")`** ([`loaders.py:47`](src/clinical_data_etl/ingestion/loaders.py)) globs both `Train-*.csv` (with `PotentialFraud`) and `Test-*.csv` (without it).
2. **Column reconciliation**: lines 67-69 detect that `PotentialFraud` is missing from the Test DataFrame and add it as `pd.NA`. This is the explicit handling I designed for: rather than letting `pd.concat` silently fill or fail, I added the missing column upfront so the downstream pandera schema sees a uniform shape.
3. **Concat**: Train + Test merged into one DataFrame.
4. **Deduplication**: providers (and beneficiaries) appear in both splits. Lines 75-86 dedup on `Provider`, keeping the Train row first so the labelled fraud flag wins over the unlabelled Test version.
5. **`validate(df, ProviderSchema, "providers")`**: lazy validation using `ProviderSchema` (lines 101-107 of `schemas.py`), which declares `PotentialFraud` as `Column(str, nullable=True)` — explicitly modelling the half-labelled reality of the data.
6. **Failure partitioning**: if any rows fail (e.g., a duplicate `Provider` slipped past dedup), `validate()` (lines 100-122) catches `pa.errors.SchemaErrors`, splits the DataFrame on the failing indices, dumps the rejects to `data/rejected/providers_rejected.csv`, and re-validates the surviving subset.
7. **`load_to_postgres`** (lines 125-146): creates the `raw` schema if missing, **drops the existing `raw.providers` table with `CASCADE`** (this is critical — dbt staging views depend on it), then `df.to_sql(... if_exists="append")`.

The same shape is used for the other three tables, controlled by the `TABLE_CONFIG` dict at the top of `loaders.py`.

### Flow 3: Raw → Staging → Intermediate → Marts

The dbt layer is a textbook three-tier model:

- **Staging** (`dbt/models/staging/`, materialised as **views**) — pure renames + type casts + value mappings. Examples:
  - `stg_beneficiary.sql` casts `"DOB"::date`, maps `"Gender"` 1/2 → `'Male'/'Female'`, maps Race codes, and converts the eleven `ChronicCond_*` 1/2 codes into `has_*` booleans.
  - `stg_providers.sql` collapses `PotentialFraud` `'Yes'/'No'` into a `boolean is_potential_fraud`, with `null` for the Test split.
  - Schema tests live in `staging/schema.yml`: uniqueness on `bene_id`/`claim_id`/`provider_id`, `not_null`s, and `accepted_values` checks on enums.
- **Intermediate** (`dbt/models/intermediate/`, also views):
  - `int_claims_unified` `UNION ALL`s the inpatient and outpatient staging models, padding the outpatient side with `NULL`s for `admission_date`, `discharge_date`, `claim_duration_days`, and `diagnosis_group_code`.
  - `int_claims_enriched` left-joins the unified claims to `stg_beneficiary` and computes `age_at_claim` via `extract(year from age(...))`.
- **Marts** (`dbt/models/marts/`, materialised as **tables** — the only persisted layer):
  - `fct_claims` — one row per claim (~558K), pulled from `int_claims_enriched`.
  - `dim_beneficiary` — one row per beneficiary, including a `chronic_condition_count` aggregate.
  - `dim_provider` — one row per provider, with the fraud label and aggregates (`total_claims`, `total_reimbursement`, `unique_beneficiaries`, `avg_reimbursement_per_claim`) computed from `int_claims_unified`.

The **fraud label deliberately stays on `dim_provider`** rather than getting denormalised onto `fct_claims`. That keeps the fact table grain clean and forces analyst queries to do the join — preserving the conceptual separation between "what happened" (claim) and "what we believe about the actor" (provider's fraud risk).

Materialisation strategy is in `dbt/dbt_project.yml`: staging + intermediate as views (cheap, recomputed on every query), marts as tables (paid once per `dbt run`, fast to query downstream). Schemas land in `raw_staging`, `raw_intermediate`, `raw_marts` because dbt prepends the target schema (`raw`) to the per-folder `+schema` overrides.

### Flow 4: Failure Handling — Rejected Rows and dbt Retries

The pipeline has two distinct failure-handling strategies, one for ingestion and one for downstream:

**Ingestion** is permissive — bad rows shouldn't kill the load. `validate()` in `loaders.py` catches `SchemaErrors`, isolates the failing row indices, writes them to `data/rejected/{table}_rejected.csv`, and continues with the survivors. The current state of `data/rejected/` shows this in action: 30 beneficiary rows, 1095 inpatient rows, and 2 test-provider rows have been quarantined across runs. The `relationships` test on `fct_claims.bene_id` in `marts/schema.yml` is set to `severity: warn` specifically because of those rejected beneficiaries — claims that point to a rejected `bene_id` are real claims I want to keep, just with a warning that the dimension lookup will be null.

**dbt steps** are unforgiving but retried. `dbt_run_task` and `dbt_test_task` both have `retries=2, retry_delay_seconds=10` ([`tasks.py:80,90`](src/clinical_data_etl/orchestration/tasks.py)). If `_run_dbt_command` returns a non-zero exit code, it raises a `RuntimeError` that includes both stdout and stderr, and Prefect retries from there. This catches the small class of transient failures (Postgres warming up, a connection blip) without hiding genuine SQL errors.

**Mart validation** is the final fail-fast: `validate_marts_task` raises `RuntimeError` if any mart table has zero rows. That covers the failure mode where dbt "succeeds" but a model silently produces no rows.

## Project History

This is a single-developer portfolio repo built across two intense April 2026 sessions. There's only one merged GitHub PR (the Claude Code GitHub Actions install on day 1) — everything else was committed directly to `main`, which is why the chronology below is built from `git log` rather than PR history.

### Milestone Summary

1. **Phase 1 — Initial scaffold** (`ce88df4`, 2026-04-02). Empty Python package skeleton, dbt project, Docker compose for Postgres, README, and a sample synthetic CSV. Just the bones.
2. **Phase 2 — Pivot to real Kaggle data** (`9ef8aa4` → `df97dda`, 2026-04-02). Replaced the synthetic NDNQI placeholder with the real four-table Medicare claims-fraud dataset and rewrote CLAUDE.md / README to describe the multi-table architecture. This was the architectural turning point — it changed the project from "trivial CSV demo" to "non-trivial multi-source pipeline with a fraud-label join problem to solve."
3. **Phase 3 — Claude Code GitHub Actions** (PR #1 `7c9b70c`, 2026-04-02). The only merged PR in the repo. Adds two workflows: `@claude` PR-comment assist and Claude Code Review.
4. **Phase 4 — Ingestion layer** (`01965ad`, 2026-04-02). Per-table pandera schemas, `load_and_merge` / `validate` / `load_to_postgres` in `loaders.py`, and the rejected-row quarantine pattern. Plus the first Python tests.
5. **Phase 5 — dbt transformation layer** (`affaf83`, 2026-04-02). The four staging models, two intermediates, three marts, and all schema tests. Star schema lands in this commit.
6. **Phase 6 — Prefect orchestration** (`a04b5a0`, 2026-04-02). `pipeline_flow` + four `@task` wrappers, the `__main__.py` CLI with `--ingest-only` / `--dbt-only` / `--full`, and tests for the orchestration layer. End-to-end runs after this.
7. **Phase 7 — CI, custom dbt tests, ERD, and CI greening** (`4301fd1` → `9c0c673`, 2026-04-04). Three-job GitHub Actions workflow (lint / typecheck / test against a real Postgres service), three custom dbt data tests, the star-schema ERD in the README, and a follow-up commit to make CI actually green (skip CSV-dependent tests when Kaggle data isn't downloaded, fix formatting, add pip cache).

### Decisions & Tradeoffs

- **Train/Test merged at ingest, not kept separate.** This is ETL, not ML — there's no model being trained downstream, so preserving the split would just be ceremony. Documented in `CLAUDE.md` and implemented in `load_and_merge` (`loaders.py:63-71`).
- **Fraud label lives on `dim_provider`, not on `fct_claims`.** Denormalising onto the fact would have made some queries simpler but corrupts the grain — claims don't have a fraud status, providers do. Kept the join honest.
- **Reject-and-continue vs fail-fast at validation.** I chose reject-and-continue, persisting rejects to `data/rejected/`. A production pipeline would probably also alert on reject volume; for a portfolio it's enough that the data exists and is auditable.
- **Materialisation: staging/intermediate as views, marts as tables.** Cheaper development loop (no staging recompute on every `dbt run`), and marts are the only thing query-side analysts touch.
- **Test split has no `PotentialFraud` column → handled with nullable schema + explicit column-add.** The alternative was to skip the Test providers entirely; I kept them because dropping ~half the providers would have made the `dim_provider` aggregates misleading.
- **`DROP TABLE ... CASCADE` in `load_to_postgres` instead of `if_exists="replace"`.** dbt's staging views depend on the raw tables. Without `CASCADE`, the second pipeline run errors. With it, the views get torn down and `dbt run` recreates them on the next step.
- **`relationships` test on `fct_claims.bene_id` set to `severity: warn`.** This was the right call given the 30 beneficiaries pandera rejects — the alternative was to either silently lose those claims or fail every CI run.
- **Subprocess to invoke dbt instead of dbt's Python API.** Trades a tiny bit of structure for a *lot* less coupling — the Prefect task knows nothing about dbt's internals; if I ever swap dbt for SQLMesh or just plain SQL files, only the `_run_dbt_command` helper changes.
- **Single-developer commits straight to `main`, not PRs.** A team wouldn't do this. For a solo portfolio piece, the PR overhead would have produced churn without any review benefit. The Claude Code review workflow is installed if I ever want to gate that way.

### Full Chronology

<details>
<summary>All commits in reverse-chronological order (12 commits)</summary>

| Commit | Date | Title |
|---|---|---|
| `9c0c673` | 2026-04-04 | fix: make CI green — skip CSV-dependent tests, add pip cache, fix formatting |
| `4301fd1` | 2026-04-04 | feat: add CI workflow, intermediate dbt tests, and star schema ERD |
| `a04b5a0` | 2026-04-02 | feat: Prefect orchestration with end-to-end pipeline flow |
| `affaf83` | 2026-04-02 | feat: dbt transformation layer with star schema marts |
| `01965ad` | 2026-04-02 | feat: ingestion layer with per-table pandera validation |
| `4d3439d` | 2026-04-02 | fix: use python3.12 for venv creation |
| `7c9b70c` | 2026-04-02 | Merge pull request #1 — Add Claude Code GitHub Workflow |
| `96d5279` | 2026-04-02 | Claude Code Review workflow |
| `1698aee` | 2026-04-02 | Claude PR Assistant workflow |
| `df97dda` | 2026-04-02 | feat: project scaffold with multi-table claims ETL architecture |
| `9ef8aa4` | 2026-04-02 | docs: update data sources from synthetic NDNQI to real Kaggle datasets |
| `ce88df4` | 2026-04-02 | feat: initial project scaffold |

The single merged PR is **#1 — Add Claude Code GitHub Workflow** (added `.github/workflows/claude-code-review.yml` and `.github/workflows/claude.yml`). Everything substantive was committed directly to `main`.

</details>

## Repository Structure

```
clinical-data-etl/
├── CLAUDE.md                          # Working instructions for Claude Code in this repo
├── PROJECT_GUIDE.md                   # This file
├── README.md                          # User-facing quickstart
├── Makefile                           # setup / db-up / pipeline / test / lint targets
├── pyproject.toml                     # Package metadata + ruff/mypy/pytest config
├── docker-compose.yml                 # postgres:16 service with healthcheck
├── .env.example                       # Shape of env vars (no secrets)
├── .github/
│   └── workflows/
│       ├── ci.yml                     # lint + typecheck + test (with real Postgres)
│       ├── claude.yml                 # @claude PR-comment assistant
│       └── claude-code-review.yml     # Auto code-review on PRs
├── src/
│   └── clinical_data_etl/
│       ├── __main__.py                # CLI entry: python -m clinical_data_etl
│       ├── ingestion/
│       │   ├── loaders.py             # load_and_merge / validate / load_to_postgres / run_ingestion
│       │   └── schemas.py             # Pandera schemas: Beneficiary, Inpatient, Outpatient, Provider
│       ├── orchestration/
│       │   ├── flows.py               # @flow pipeline_flow
│       │   └── tasks.py               # @task ingest / dbt_run / dbt_test / validate_marts
│       └── utils/
│           └── db.py                  # SQLAlchemy engine factory
├── dbt/
│   ├── dbt_project.yml                # Materialisation strategy by folder
│   ├── profiles.yml                   # postgres adapter, env-var-driven
│   ├── models/
│   │   ├── staging/                   # 4 stg_* views + schema.yml + src_raw.yml
│   │   ├── intermediate/              # int_claims_unified, int_claims_enriched
│   │   └── marts/                     # fct_claims, dim_beneficiary, dim_provider
│   └── tests/                         # 3 custom data tests (singular SQL queries)
├── tests/
│   ├── test_ingestion/                # Pandera schema unit tests + loader tests
│   └── test_orchestration/            # Flow + task tests with mocked dependencies
└── data/
    ├── raw/                           # gitignored — Kaggle CSVs land here
    └── rejected/                      # Quarantined rows that failed pandera validation
```

(Skipped: `.venv/`, `dbt/target/`, `dbt/logs/`, `__pycache__/`, `*.egg-info/`.)

## User Guide

### Prerequisites

- **Python 3.11+** (the `Makefile` `setup` target specifically uses `python3.12` — adjust if you don't have it).
- **Docker + Docker Compose** to run Postgres locally.
- **Kaggle CLI** (`pip install kaggle`) with API credentials configured at `~/.kaggle/kaggle.json` — the data isn't redistributable so it isn't checked in.
- **Git** to clone.

### Installation

```bash
git clone https://github.com/ksdisch/clinical-data-etl.git
cd clinical-data-etl
make setup           # creates .venv with python3.12 and pip-installs the package + dev extras
```

If you don't have Python 3.12, the manual equivalent is:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configuration

All configuration is environment-variable driven. Copy the template and edit if your setup differs:

```bash
cp .env.example .env
```

Variables (all consumed by both the Python loader and dbt's `profiles.yml`):

| Var | Default | What it's for |
|---|---|---|
| `POSTGRES_DB` | `clinical_etl` | Database name |
| `POSTGRES_USER` | `etl_user` | Database user |
| `POSTGRES_PASSWORD` | `etl_pass` | Database password |
| `POSTGRES_HOST` | `localhost` | Hostname Postgres listens on |
| `POSTGRES_PORT` | `5432` | Port |
| `DATABASE_URL` | `postgresql://etl_user:etl_pass@localhost:5432/clinical_etl` | SQLAlchemy connection string used by `utils/db.py` |

For the defaults to work, leave `docker-compose.yml` alone — they match.

### Running Locally

The minimum sequence for a clean machine:

```bash
make setup                    # 1. install
make download-data            # 2. pull Kaggle datasets to data/raw/
make db-up                    # 3. start Postgres in Docker
cd dbt && dbt debug && cd ..  # 4. (optional) verify dbt connection
make pipeline                 # 5. run the whole thing
```

Expected output (abridged):

```
Step 1/4: Ingesting claims data...
  raw.beneficiary: 138526 loaded, 30 rejected
  raw.inpatient_claims: 39187 loaded, 1095 rejected
  raw.outpatient_claims: 519441 loaded, 0 rejected
  raw.providers: 5408 loaded, 2 rejected
Step 2/4: Running dbt models...   [ 9 of 9 OK ]
Step 3/4: Running dbt tests...    [ 28 PASS, 1 WARN ]
Step 4/4: Validating mart tables...
  raw_marts.fct_claims: 558628 rows
  raw_marts.dim_beneficiary: 138526 rows
  raw_marts.dim_provider: 5408 rows
Pipeline completed in 36.0 seconds
```

### Usage Examples

```bash
# Full pipeline
make pipeline
python -m clinical_data_etl --full

# Just re-ingest from CSVs (skips dbt)
make pipeline-ingest
python -m clinical_data_etl --ingest-only

# Just re-run dbt (skips ingest — useful when you change a model)
make pipeline-dbt
python -m clinical_data_etl --dbt-only

# Run dbt commands directly
cd dbt && dbt run && dbt test
cd dbt && dbt build --select stg_beneficiary+   # rebuild bene + everything downstream
cd dbt && dbt docs generate && dbt docs serve   # browse the lineage graph

# Tests + lint
make test
make lint

# Stop Postgres (volume persists in the pgdata Docker volume)
make db-down
```

Inspect the marts directly:

```bash
docker exec -it clinical_etl_db psql -U etl_user -d clinical_etl
# In psql:
\dn                                          -- list schemas
\dt raw_marts.*                              -- list mart tables
SELECT COUNT(*), is_potential_fraud
  FROM raw_marts.dim_provider
  GROUP BY 1;
```

### Common Workflows

- **Iterating on a dbt model**: edit the `.sql` file, then `make pipeline-dbt` to recompute everything downstream and rerun tests.
- **Iterating on a pandera schema**: edit `src/clinical_data_etl/ingestion/schemas.py`, then `pytest tests/test_ingestion/test_schemas.py -v`. The schema unit tests don't need Postgres or the Kaggle CSVs.
- **Inspecting rejected rows**: open `data/rejected/{table}_rejected.csv` after a pipeline run.
- **Adding a new dbt test**: drop a `.sql` file into `dbt/tests/` that returns rows when the assertion fails (existing examples: `assert_age_at_claim_valid.sql`, `assert_claim_dates_ordered.sql`, `assert_reimbursement_non_negative.sql`).

### Troubleshooting

- **`PostgreSQL not available — run \`make db-up\`** (skipped tests). The integration test in `test_loaders.py` autoskips when it can't connect; bring Docker up.
- **`No train files matching ... in .../data/raw/claims_fraud`** raised by `load_and_merge`. The Kaggle datasets aren't downloaded — run `make download-data`.
- **dbt step fails with "relation does not exist"** — usually means the `raw` tables haven't been loaded. Run `make pipeline-ingest` first.
- **`dbt run failed (exit N)`** in a Prefect log. The full dbt stdout/stderr is included in the `RuntimeError` message; scroll up in the Prefect log block. The task will retry twice automatically.
- **`Mart table raw_marts.X is empty!`** raised by `validate_marts_task`. Indicates an upstream model produced zero rows — usually a join condition or a schema-prefix mismatch. Inspect `dbt/target/run_results.json` and the corresponding intermediate model.
- **CI-only failure: schema/loader tests skipped on CI.** This is intentional — the Kaggle CSVs aren't downloaded in CI. Schema unit tests still run; the integration tests don't.

### Deployment

This project doesn't deploy. Postgres runs in a local Docker container (`docker-compose.yml`); Prefect runs as a local flow execution; there is no `Dockerfile` for the application, no Helm chart, no Terraform, no Prefect deployment manifest. If I were to productionise it, the natural shape would be a Prefect deployment running on a worker pool with Postgres swapped for a managed warehouse and `data/raw/` swapped for an object-storage source.

---

## Footer

Last updated: 2026-05-15
Generated by Claude Code from commit `9c0c673`.
