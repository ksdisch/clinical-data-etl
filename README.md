# Clinical Data ETL Pipeline

A multi-source clinical data ETL pipeline that ingests two heterogeneous healthcare datasets — Medicare claims fraud detection (4 related CSV tables) and UCI diabetes-readmission hospital encounters — validates each with pandera, stages into PostgreSQL, transforms with dbt into **two independent star schemas**, and orchestrates with Prefect.

Built as a portfolio project for Data Engineering / Analytics Engineering roles.

[![CI](https://github.com/ksdisch/clinical-data-etl/actions/workflows/ci.yml/badge.svg)](https://github.com/ksdisch/clinical-data-etl/actions/workflows/ci.yml)

## Architecture

```
  data/raw/claims_fraud/
  ┌──────────────────────────────────────────────┐
  │  Train + Test Beneficiary CSVs               │
  │  Train + Test Inpatient Claims CSVs          │
  │  Train + Test Outpatient Claims CSVs         │
  │  Train + Test Provider Labels CSVs           │
  └──────────────────┬───────────────────────────┘
                     ▼
  ┌──────────────────────────────────────────────┐
  │  Ingestion (Python)                          │
  │  Per-table pandera schemas                   │
  │  Merge Train/Test splits → single tables     │
  │  Nullable fraud flag for Test providers      │
  └──────────────────┬───────────────────────────┘
                     ▼
  ┌──────────────────────────────────────────────┐
  │  PostgreSQL — raw schema                     │
  │  raw.beneficiary                             │
  │  raw.inpatient_claims                        │
  │  raw.outpatient_claims                       │
  │  raw.providers                               │
  └──────────────────┬───────────────────────────┘
                     ▼
  ┌──────────────────────────────────────────────┐
  │  dbt — staging → intermediate → marts        │
  │                                              │
  │  staging:      stg_beneficiary               │
  │                stg_inpatient_claims           │
  │                stg_outpatient_claims          │
  │                stg_providers                  │
  │                                              │
  │  intermediate: int_claims_unified              │
  │                int_claims_enriched             │
  │                                              │
  │  marts:        fct_claims                    │
  │                dim_beneficiary               │
  │                dim_provider (+ fraud label)   │
  └──────────────────────────────────────────────┘

  Orchestrated by Prefect
```

## Star Schema ERD

```
┌─────────────────────────────┐
│       dim_beneficiary       │
├─────────────────────────────┤
│ bene_id              (PK)   │
│ date_of_birth               │
│ date_of_death               │
│ gender                      │
│ race                        │
│ state_code                  │
│ county_code                 │
│ has_alzheimers  ... (×11)   │
│ chronic_condition_count     │
│ total_ip_reimbursement      │
│ total_op_reimbursement      │
└──────────────┬──────────────┘
               │ bene_id
               │
┌──────────────┴──────────────┐
│          fct_claims         │
├─────────────────────────────┤
│ claim_id             (PK)   │
│ bene_id              (FK)───┘
│ provider_id          (FK)───┐
│ claim_type                  │
│ claim_start_date            │
│ claim_end_date              │
│ admission_date              │
│ discharge_date              │
│ claim_duration_days         │
│ reimbursement_amount        │
│ deductible_amount           │
│ age_at_claim                │
│ diagnosis_code_1 ... (×10)  │
│ procedure_code_1 ... (×6)   │
└──────────────┬──────────────┘
               │ provider_id
               │
┌──────────────┴──────────────┐
│        dim_provider         │
├─────────────────────────────┤
│ provider_id          (PK)   │
│ is_potential_fraud          │
│ total_claims                │
│ total_reimbursement         │
│ unique_beneficiaries        │
│ avg_reimbursement_per_claim │
└─────────────────────────────┘
```

## Diabetes Star Schema ERD (second source)

The diabetes-readmission data is modelled as a second, independent star — same
patterns, different domain. There is no key joining it to the claims data.

```
┌─────────────────────────────┐      ┌─────────────────────────────┐
│         dim_patient         │      │     dim_admission_type      │
├─────────────────────────────┤      ├─────────────────────────────┤
│ patient_nbr          (PK)   │      │ admission_type_id    (PK)   │  ← dbt seed
│ race                        │      │ admission_type_label        │
│ gender                      │      └──────────────┬──────────────┘
│ latest_age_bracket          │                     │ admission_type_id
│ total_encounters            │                     │
│ num_readmissions_30d        │      ┌──────────────┴──────────────┐
│ readmission_30d_rate        │      │       fct_encounters        │
└──────────────┬──────────────┘      ├─────────────────────────────┤
               │ patient_nbr         │ encounter_id         (PK)   │
               └─────────────────────│ patient_nbr          (FK)   │
                                     │ admission_type_id    (FK)   │
                                     │ time_in_hospital            │
                                     │ num_lab_procedures          │
                                     │ num_prior_visits            │
                                     │ num_diabetes_meds           │
                                     │ diag_1 ... diag_3           │
                                     │ insulin / metformin         │
                                     │ readmitted_status           │
                                     │ is_readmitted_30d           │
                                     └─────────────────────────────┘
```

## Data Lineage

The dbt project builds 15 models across three layers (10 for the claims star, 5
for the diabetes star). Run `make dbt-docs` to generate and serve the interactive
lineage graph; the same dependency structure is shown below.

```mermaid
flowchart LR
    subgraph raw["raw schema (PostgreSQL)"]
        r_bene[(beneficiary)]
        r_inp[(inpatient_claims)]
        r_outp[(outpatient_claims)]
        r_prov[(providers)]
        r_diab[(diabetes_encounters)]
    end
    subgraph staging
        s_bene[stg_beneficiary]
        s_inp[stg_inpatient_claims]
        s_outp[stg_outpatient_claims]
        s_prov[stg_providers]
        s_diab[stg_diabetes_encounters]
        seed_at[/admission_type_mapping seed/]
    end
    subgraph intermediate
        i_uni[int_claims_unified]
        i_enr[int_claims_enriched]
        i_enc[int_encounters_enriched]
    end
    subgraph marts
        m_fct[fct_claims]
        m_bene[dim_beneficiary]
        m_prov[dim_provider]
        m_enc[fct_encounters]
        m_pat[dim_patient]
        m_adm[dim_admission_type]
    end

    r_bene --> s_bene
    r_inp --> s_inp
    r_outp --> s_outp
    r_prov --> s_prov
    r_diab --> s_diab

    s_inp --> i_uni
    s_outp --> i_uni
    i_uni --> i_enr
    s_bene --> i_enr
    i_enr --> m_fct
    s_bene --> m_bene
    s_prov --> m_prov
    i_uni --> m_prov

    s_diab --> i_enc
    i_enc --> m_enc
    s_diab --> m_pat
    seed_at --> m_adm
```

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [Kaggle CLI](https://github.com/Kaggle/kaggle-api) (`pip install kaggle`) with API credentials configured
- Git

## Setup

### 1. Clone and install

```bash
git clone https://github.com/ksdisch/clinical-data-etl.git
cd clinical-data-etl
make setup
```

Or manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Download data

> Requires Kaggle API credentials: place your `kaggle.json` token at `~/.kaggle/kaggle.json` and run `chmod 600 ~/.kaggle/kaggle.json`. See the [Kaggle API docs](https://github.com/Kaggle/kaggle-api#api-credentials).

```bash
make download-data
```

Or manually:

```bash
kaggle datasets download -d rohitrox/healthcare-provider-fraud-detection-analysis -p data/raw/claims_fraud/ --unzip
kaggle datasets download -d brandao/diabetes -p data/raw/diabetes_readmission/ --unzip
kaggle datasets download -d amulyas/synthetic-hospital-data -p data/raw/synthetic_hospital/ --unzip
```

### 3. Start PostgreSQL

```bash
cp .env.example .env   # edit credentials if needed
make db-up
```

### 4. Verify dbt connection

```bash
cd dbt && dbt debug && cd ..
```

### 5. Run the pipeline

```bash
make pipeline
```

## Project Structure

```
src/clinical_data_etl/    Python package (ingestion, orchestration, utils)
dbt/                      dbt project (staging, intermediate, marts models)
tests/                    pytest test suite
data/raw/                 Kaggle datasets (gitignored — see setup instructions)
```

## Makefile Targets

| Target          | Description                                 |
|-----------------|---------------------------------------------|
| `make setup`    | Create venv and install package with dev deps |
| `make download-data` | Download all Kaggle datasets            |
| `make db-up`    | Start PostgreSQL container                  |
| `make db-down`  | Stop PostgreSQL container                   |
| `make test`     | Run pytest                                  |
| `make lint`     | Run ruff linter                             |
| `make pipeline` | Run full ETL pipeline (idempotent: upsert ingest + snapshot + incremental dbt + test) |
| `make pipeline-reset` | Clean rebuild: TRUNCATE raw (snapshots survive) + dbt `--full-refresh` |
| `make pipeline-ingest` | Ingestion only (CSV → PostgreSQL)      |
| `make pipeline-dbt` | dbt only (transform + test)               |
| `make demo-incremental` | Self-verifying proof of incremental adds + idempotency |
| `make demo-scd2` | Self-verifying proof of SCD2 fraud-label history (seeded vintage) |
| `make dbt-compile` | Compile dbt models (validate SQL, no DB writes) |
| `make dbt-docs` | Generate and serve dbt docs + lineage graph     |

## Tech Stack

- **Python** (pandas, pandera) — ingestion and validation
- **PostgreSQL 16** — data warehouse (via Docker)
- **dbt** (dbt-postgres) — SQL transformations and testing
- **Prefect** — workflow orchestration
- **pytest, ruff, mypy** — testing and code quality

## Roadmap

MVP complete as of April 2026. The pipeline ingests both sources end-to-end in well under a minute, passes 47 pytest tests and 71 dbt tests (70 pass, 1 expected warn on the orphan-claims relationship).

**Production-shaping (done):** the warehouse uses an **idempotent ON CONFLICT upsert** loader (no more DROP+reload), **incremental** `int_claims_enriched`/`fct_claims`/`fct_encounters` models, and **SCD Type 2** history on the provider fraud label (`snap_provider_fraud` → `dim_provider_history`). Because the claims data is single-vintage, incrementality and history are demonstrated with deterministic, seeded inputs via `make demo-incremental` and `make demo-scd2`. See [`docs/incremental_scd2.md`](docs/incremental_scd2.md).

**Phase 2 — second source (done):** the UCI diabetes-readmission dataset (`brandao/diabetes`, 101,766 encounters, 50 columns) is now wired through the full pipeline as a second, independent star schema — `stg_diabetes_encounters` → `int_encounters_enriched` → `fct_encounters` (incremental) + `dim_patient` + a seed-backed `dim_admission_type`. The `?` missing sentinel is recoded to NULL before pandera validation; the analytical target is 30-day readmission. See [`docs/phase2-diabetes-plan.md`](docs/phase2-diabetes-plan.md).

Phase 2 (remaining, deferred): the tertiary synthetic-hospital dataset and Tier 3 docs (ADR directory, full data dictionary).
