# Clinical Data ETL Pipeline

## Project Overview

A portfolio project demonstrating Data Engineering and Analytics Engineering skills through a multi-source clinical data ETL pipeline. The pipeline ingests two real Kaggle healthcare datasets — Medicare claims fraud detection (4 related CSV tables) and UCI diabetes-readmission hospital encounters (1 CSV) — validates each table with pandera, stages into PostgreSQL, transforms with dbt into two independent star schemas, and orchestrates the workflow with Prefect.

This project exists to showcase:
- Multi-source, multi-table ETL pipeline design and implementation
- Data quality validation with per-table pandera schemas
- Dimensional modeling and analytics engineering with dbt
- Workflow orchestration and error handling
- Infrastructure-as-code with Docker

### Data Sources

- **PRIMARY**: Medicare Claims Fraud Detection (`data/raw/claims_fraud/`) — 4 tables: beneficiary, inpatient_claims, outpatient_claims, providers; each has Train+Test CSVs merged at ingest. The Test Provider CSV has no `PotentialFraud` column; loader adds `NaN`.
- **SECONDARY** (WIRED): Diabetes Readmission (`data/raw/diabetes_readmission/diabetic_data.csv`) — single CSV, 101,766 encounters, grain `encounter_id`. The `?` missing sentinel is recoded to NULL before validation. Modelled as a second, independent star (`fct_encounters` + `dim_patient` + seed-backed `dim_admission_type`).
- **TERTIARY** (Phase 2): Synthetic Hospital (`data/raw/synthetic_hospital/`)

Full CSV filenames and column descriptions: [`docs/data-sources.md`](docs/data-sources.md)

## Tech Stack

| Tool         | Purpose                  | Version       |
|-------------|--------------------------|---------------|
| Python       | Core language            | 3.11+         |
| pandas       | Data manipulation        | 2.x           |
| pandera      | Schema validation        | 0.18+         |
| PostgreSQL   | Data warehouse           | 16 (Docker)   |
| dbt-core     | Transformation layer     | 1.10+         |
| dbt-postgres | dbt adapter              | 1.10+         |
| Prefect      | Orchestration            | 2.x           |
| Docker       | PostgreSQL hosting       | -             |
| pytest       | Testing                  | 8.x           |

## Architectural Decisions

### Scope
- **MVP**: `claims_fraud` dataset. **Phase 2 (done)**: `diabetes_readmission` wired as a second source/star. Synthetic hospital remains Phase 2.

### Ingestion
- Train/Test CSV splits are **merged during ingestion** (this is ETL, not ML). Both files per table validate against the same pandera schema, get concatenated, and load into one raw table.
- The Test Provider file (`Test-1542969243754.csv`) has **no PotentialFraud column**. Handle gracefully: the pandera `ProviderSchema` allows a nullable fraud flag, and the loader adds `PotentialFraud = NaN` when the column is missing.

### Modeling
- **Claims star**: `fct_claims` (grain: one row per claim), `dim_beneficiary` (one row per beneficiary), `dim_provider` (one row per provider, includes fraud label).
- Fraud label stays in `dim_provider`, **NOT** denormalized onto `fct_claims`.
- **Diabetes star** (second source): `fct_encounters` (grain: one row per `encounter_id`, incremental), `dim_patient` (one row per `patient_nbr`, demographics from latest encounter + readmission rollups), `dim_admission_type` (seed-backed lookup). No key joins the two stars — they are deliberately independent.

## Architecture

```
CSV files (4 claims_fraud tables + diabetes encounters [+ synthetic, Phase 2])
  │
  ▼
Ingestion (pandas + per-table pandera schemas)
  │  Beneficiary CSV ──→ pandera BeneficiarySchema
  │  Inpatient CSV   ──→ pandera InpatientClaimSchema
  │  Outpatient CSV  ──→ pandera OutpatientClaimSchema
  │  Provider CSV    ──→ pandera ProviderSchema
  │  Diabetes CSV    ──→ pandera DiabetesEncounterSchema  ('?' → NA first)
  │
  ▼
PostgreSQL raw schema
  │  raw.beneficiary, raw.inpatient_claims,
  │  raw.outpatient_claims, raw.providers
  │  raw.diabetes_encounters
  │
  ▼
dbt Transforms  (two independent stars)
  ├── staging   (stg_beneficiary, stg_inpatient_claims, stg_outpatient_claims,
  │              stg_providers, stg_diabetes_encounters)
  ├── seeds     (admission_type_mapping)
  ├── intermediate (int_claims_unified, int_claims_enriched,
  │              int_encounters_enriched)
  └── marts     claims:   fct_claims, dim_beneficiary, dim_provider,
  │                       dim_provider_history (SCD2)
  │             diabetes: fct_encounters, dim_patient, dim_admission_type
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

`src/clinical_data_etl/{ingestion,orchestration,utils}/` · `dbt/models/{staging,intermediate,marts}/` + `dbt/{snapshots,seeds,macros,tests}/` · `tests/{test_ingestion,test_utils}/` · `data/raw/{claims_fraud,diabetes_readmission,synthetic_hospital}/`

Annotated layout: [`docs/data-sources.md`](docs/data-sources.md)

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

## Claude tooling for this repo

Commands and skills vendored into `.claude/` so they work in cloud/web sessions and for collaborators. Invoke a command with `/<name>`; skills auto-trigger or can be invoked by name. All items below are cloud-safe (pure reasoning + repo edits — no local-only browser/MCP dependencies).

### Commands (`.claude/commands/`)
- **`/explore-plan`** — Explore → plan → confirm before any code; proposes 2–3 ranked approaches and waits for you to pick.
- **`/tdd`** — Test-first loop: write failing tests for a spec, confirm they fail, then code until green without modifying the tests.
- **`/handoff`** — Generate a self-contained handoff prompt to continue the work in a fresh session; captures lessons + plan state.
- **`/wrap`** — End-of-session recap with active-recall quiz and next moves; saves a dated log.
- **`/begin`** — Session-start orientation: branch, recent commits, open PRs, recap from the last `/wrap` log.
- **`/trim-context`** — Find and fix Claude Code token bloat (oversized CLAUDE.md vs the 40k limit, bloated memory, `.claude/` cruft).
- **`/autonomous-milestone`** — Plan/build/test/verify a milestone end-to-end, or triage the backlog into ranked candidates. Uses multi-agent orchestration (higher cost).

### Skills (`.claude/skills/`)
- **`artifacts-audit`** — Audit the repo for which engineering artifacts (ADRs, runbooks, ERDs, design docs) it should have; writes `docs/artifacts-plan.md`. Plans only, no source changes.
- **`artifacts-generate`** — Generate the artifacts from that plan (READMEs, ADRs, ERDs, runbooks). Companion to `artifacts-audit`.
- **`new-dbt-model`** — Scaffold a dbt model to this repo's conventions (layer + `stg_/int_/fct_/dim_` prefix, paired `schema.yml` tests, the `delete+insert` incremental config pattern). Invoke with `/new-dbt-model`.
- **`add-source`** — Wire a new raw source end-to-end (pandera schema → upsert loader → `raw` table → staging → independent star), following the diabetes path. Invoke with `/add-source`.

### Subagents (`.claude/agents/`)
- **`dbt-model-reviewer`** — Reviews dbt changes against this repo's modeling rules (grain integrity, fraud label stays in `dim_provider`, incremental boundary, tests present). Read-only.
- **`analytics-sql-reviewer`** — Audits SQL correctness (join fan-out/grain explosions, NULL handling on recoded columns, window-function partitioning, divide-by-zero in rate columns). Read-only.

### Hooks (`.claude/settings.json` → `.claude/hooks/`)
- **`ruff-on-edit.sh`** (PostToolUse on `Edit|Write|MultiEdit`) — auto-runs `ruff format` + `ruff check --fix` on edited `.py` files so the CI `ruff format --check` gate stays green; surfaces any unfixable lint back to Claude. Cloud-safe.
- **`dbt-parse-on-model-edit.sh`** (same trigger) — runs `dbt parse` after editing dbt SQL to catch ref/Jinja/version-API drift before push. DB-free (profiles have `env_var` defaults), so cloud-safe; skips silently if `dbt` isn't installed.

### MCP servers (`.mcp.json`) — 💻 local-only, won't run in cloud/web sessions
- **`postgres`** (`uvx postgres-mcp --access-mode=restricted`) — read-only query access to the warehouse for inspecting `raw.*`/`marts.*` and verifying marts. Connects via `POSTGRES_*` env vars (defaults to the local dev DB on port **5433**). Needs the running Postgres + `uvx`.
- **`dbt`** (`uvx dbt-mcp`) — dbt CLI tools (run/test/compile/lineage) over the local project; dbt Cloud features disabled. Needs the local dbt project, DB, and `uvx`. Package/env names may need tweaking per `dbt-mcp` version.

## Current Priority

**Phase 2 second-source milestone complete** (diabetes-readmission wired as an independent star), on top of the production-shaping milestone (incremental models + idempotent backfills + SCD2 history) and the MVP. Next: consider the tertiary synthetic-hospital dataset or Tier 3 docs.

### What works now
- `make pipeline` — idempotent end-to-end across **both sources**: upsert ingest → `dbt seed` → `dbt snapshot` → incremental `dbt run` (15 models) → `dbt test` → validate marts (both stars). Re-running is a no-op; raw tables accumulate via `ON CONFLICT` (no more DROP+reload).
- `make pipeline-reset` — clean rebuild: TRUNCATE raw (snapshots survive) + `dbt run --full-refresh`
- `make pipeline-ingest` / `make pipeline-dbt` — ingestion only / dbt only
- `make demo-incremental` / `make demo-scd2` — self-verifying, seeded proofs of incremental adds and SCD2 history (see [`docs/incremental_scd2.md`](docs/incremental_scd2.md))
- `python -m clinical_data_etl [--ingest-only | --dbt-only | --full] [--reset]`
- 47 pytest tests pass; 71 dbt tests (70 pass, 1 expected warn on the orphan-claims relationship)

### Diabetes second-source notes (Phase 2)
- Single CSV (no train/test merge); `clean_diabetes_frame` recodes the `?` sentinel → NA before pandera `DiabetesEncounterSchema` validation. Loaded to `raw.diabetes_encounters` via the same `load_to_postgres` upsert (`key='encounter_id'`).
- Star: `stg_diabetes_encounters` → `int_encounters_enriched` (view, derives `num_prior_visits`/`num_diabetes_meds`) → `fct_encounters` (incremental, `unique_key='encounter_id'`) + `dim_patient` (table) + `dim_admission_type` (from `dbt/seeds/admission_type_mapping.csv` — first use of seeds).
- Analytical target: 30-day readmission (`is_readmitted_30d` = `readmitted_status == '<30'`); overall rate ~11%. Single-vintage (1999–2008) so framed as descriptive feature engineering, not a deployed model.

### Incremental / SCD2 design notes (important)
- Incremental boundary: `int_claims_unified` stays a **full view** (because `dim_provider` aggregates over it); only `int_claims_enriched` + `fct_claims` are `materialized='incremental'` (`unique_key='claim_id'`, `delete+insert`).
- SCD2: `dbt/snapshots/snap_provider_fraud.sql` (check strategy on `is_potential_fraud`, reads `source('raw','providers')`) → `dim_provider_history` mart, with no-overlap / one-current invariant tests in `dbt/tests/`.
- The data is single-vintage (~2009), so incrementality and history are demonstrated with **deterministic seeded** inputs (hash-bucketed claims; a seeded fraud-flag flip) — framed honestly as seeded demos, not real CDC.
- Loader: `load_to_postgres(..., mode='upsert'|'replace')` stamps a first-seen `ingested_at` (never overwritten on conflict) and ensures a unique index per natural key.
