# Operational-Runbook

## Purpose
What runs, in what order, what fails how, and what to check first. This page
synthesizes the Prefect flow step sequence, Makefile targets, failure modes buried in
the task code, and the reset-vs-upsert design. No single document covers all of this:
the README has the Makefile table, `docs/incremental_scd2.md` has the demo commands,
and the Prefect flow code holds the authoritative step order and failure behavior —
but none of them explain how they fit together for operations.

## Key understanding

### Pipeline step order (authoritative)

**Fact** (from `src/clinical_data_etl/orchestration/flows.py` — `pipeline_flow`):

```
Step 1/6  ingest_task(mode=upsert|replace)
Step 2/6  dbt_seed_task        — load lookup seeds (admission_type_mapping, severity_mapping)
Step 3/6  dbt_snapshot_task    — build SCD2 snapshot (snap_provider_fraud)
Step 4/6  dbt_run_task         — run all 20 dbt models (incremental by default)
Step 5/6  dbt_test_task        — 98 dbt tests (97 pass / 1 expected warn)
Step 6/6  validate_marts_task  — row-count check on all 10 mart tables
```

**Inference** (from the step order + `dbt_snapshot_task` docstring): The snapshot runs
**before** `dbt run` so that `dim_provider_history` (which reads the snapshot relation)
can build successfully. If you run `dbt run` without first running `dbt snapshot`, the
snapshot relation may not exist and `dim_provider_history` will fail.

**Fact** (from `tasks.py` — `dbt_seed_task` docstring): Seeds must run before `dbt run`
so seed-backed models (`dim_admission_type`, `dim_severity`) can build. A `dbt run`
without a prior `dbt seed` will fail on these two mart models.

### Makefile targets and what they actually do

**Fact** (from `Makefile` and `src/clinical_data_etl/orchestration/flows.py`):

| Target | What it does |
|---|---|
| `make pipeline` | Full flow: upsert ingest → seed → snapshot → incremental dbt run → dbt test → validate marts. Idempotent — re-run in ~1 min. |
| `make pipeline-reset` | Cleans raw tables (TRUNCATE, not DROP) then full-refresh dbt run. Snapshots **survive** the TRUNCATE. Dependent dbt views also survive (no CASCADE). |
| `make pipeline-ingest` | Ingestion only (CSV → raw); skips dbt entirely. |
| `make pipeline-dbt` | dbt only (seed → snapshot → run → test); skips ingestion. |
| `make demo-incremental` | Deterministic proof of incremental behavior: hash-bucket partition → first load → incremental load → idempotency assertion. Self-restoring. |
| `make demo-scd2` | Deterministic proof of SCD2: flip fraud flags on a fixed provider set → re-snapshot → assert second version rows. Self-restoring (baseline restored at end). |
| `make dbt-compile` | Compile only — validates SQL/Jinja/refs without writing to the DB. Safe to run without a live DB. |
| `make dbt-docs` | Generate and serve dbt lineage docs on localhost (requires live DB). |

### Failure modes and what to check first

**Fact** (from `tasks.py` — `_run_dbt_command`, `validate_marts_task`): dbt tasks raise
`RuntimeError` with the full stdout/stderr on non-zero exit. `validate_marts_task`
raises `RuntimeError("Mart table ... is empty!")` if any of the 10 mart tables has
zero rows.

**Inference** (from code + step order): Common failure patterns and first checks:

| Symptom | Most likely cause | First check |
|---|---|---|
| `dbt run` fails on `dim_admission_type` or `dim_severity` | Seeds not loaded | Run `dbt seed` manually or use `make pipeline` (seeds run at step 2) |
| `dbt run` fails on `dim_provider_history` | Snapshot not yet built | Run `dbt snapshot` manually before `dbt run` |
| `validate_marts_task` fails: mart table is empty | Ingestion wasn't run first, or raw table is empty | Check `raw.*` table row counts; run `make pipeline-ingest` first |
| `make pipeline` hangs for > 2 min on incremental models | Incremental boundary is `NOT IN` instead of `NOT EXISTS` | Check `int_claims_enriched.sql` and `fct_claims.sql` for the correct anti-join form (ADR-006) |
| pandera raises `SchemaErrors` and aborts | A source CSV changed format (new column, renamed column, missing column) | Check `data/rejected/<table>_rejected.csv` for the failed rows; validate the column set against `schemas.py` |
| Provider Test split load fails | Kaggle re-download re-added the `PotentialFraud` column to the Test file | `load_and_merge` in `loaders.py` handles this gracefully only for the missing-column case; a column-type change would require a schema update |

### upsert vs. replace: what survives each mode

**Fact** (from `loaders.py` — `load_to_postgres` and `reset_raw_tables`):

- **upsert** (default): `INSERT ... ON CONFLICT DO UPDATE`. Raw tables accumulate. The
  `ingested_at` column is stamped on first insert and never overwritten — re-loading
  identical data changes nothing.
- **replace**: TRUNCATE the raw table first, then load. TRUNCATE (not DROP CASCADE) means:
  - dbt **views** (`stg_*`, intermediate views) survive — they are not dropped.
  - The dbt **snapshot table** (`snap_provider_fraud`) survives — it is DB-resident and
    not a dependent view.
  - dbt **incremental tables** are **not** affected by the raw TRUNCATE; they still hold
    old rows until `dbt run --full-refresh` is called. `make pipeline-reset` handles
    this by running `full_refresh=True` in `dbt_run_task`.

**Inference**: If you TRUNCATE raw without also running `dbt run --full-refresh`, the
incremental mart tables will retain stale rows that no longer have a corresponding raw
source. The `pipeline-reset` target is the only safe full-rebuild path.

### Row-count fitness functions (verified)

**Fact** (from `docs/incremental_scd2.md` — "Verified fitness functions"):
- `fct_claims`: 693,603 rows (default pipeline and pipeline-reset).
- `dim_provider_history`: 6,763 rows.
- `make demo-incremental`: 5/5 assertions pass.
- `make demo-scd2`: 4/4 assertions pass, baseline restored.
- dbt test: PASS=45 / WARN=1 (the expected orphan-claims relationship) / ERROR=0.
  (Note: an older count; total dbt tests is 98 per README — the fitness function
  was recorded at an earlier test count.)

**Inference**: The README and `CLAUDE.md` report 98 total dbt tests; the fitness
functions in `incremental_scd2.md` report the older 45/1 breakdown. The total test
count grew as Phase 2 and Phase 3 tests were added — the 97-pass/1-warn
characterization in `CLAUDE.md` is the current state.

### dbt invocation mechanism

**Fact** (from `tasks.py` — `_run_dbt_command`): dbt is invoked as a subprocess using
the `dbt` binary from the **same Python venv** as the running Prefect process
(`Path(sys.executable).parent / "dbt"`). This means:
- dbt is not installed globally; it runs from the project venv.
- `--profiles-dir` and `--project-dir` are always passed explicitly, pointing to `dbt/`.
- The ADR-009 decision records why subprocess was chosen over Python dbt-core import.

**Fact** (from `dbt/profiles.yml` and CLAUDE.md): The dbt profile uses `env_var`
defaults for DB connection, so `dbt parse` / `dbt compile` work without a live DB
(environment defaults to empty strings). `dbt run` and `dbt test` require the live DB.

## Sources
- `src/clinical_data_etl/orchestration/flows.py` — authoritative step order for the pipeline flow
- `src/clinical_data_etl/orchestration/tasks.py` — task implementation, failure behavior, subprocess invocation
- `src/clinical_data_etl/ingestion/loaders.py` — upsert vs replace semantics, TRUNCATE-not-DROP behavior
- `Makefile` — the target definitions and their command sequences
- [`docs/incremental_scd2.md`](../docs/incremental_scd2.md) — demo mechanics and verified fitness functions
- [`docs/adr/006-incremental-boundary-not-exists.md`](../docs/adr/006-incremental-boundary-not-exists.md) — why NOT EXISTS (not NOT IN) and the >14-min hang context
- [`docs/adr/009-subprocess-dbt-invocation.md`](../docs/adr/009-subprocess-dbt-invocation.md) — why dbt runs as subprocess

## Uncertainties & contradictions
- **Contradiction:** `docs/incremental_scd2.md` reports fitness function dbt counts of PASS=45/WARN=1; `CLAUDE.md` and README report 98 total dbt tests (97 pass / 1 expected warn). **Inference:** the fitness functions were recorded before Phase 2 and Phase 3 tests were added. The 97/1 numbers in CLAUDE.md are current.
- **Unresolved:** `validate_marts_task` queries `raw_marts.*` (hardcoded schema name in tasks.py). If the dbt target profile uses a different schema name for a given environment, `validate_marts_task` will fail with a table-not-found error even when marts built successfully. Verify the actual dbt target schema matches `raw_marts` in the environment being used.
- **Unresolved:** Prefect retry configuration — `dbt_seed_task`, `dbt_snapshot_task`, `dbt_run_task`, and `dbt_test_task` each have `retries=2, retry_delay_seconds=10`. There is no documentation of what errors are safe to retry (transient DB connection vs. real dbt model failure). A real model failure will be retried twice before raising, which can delay surfacing the error.

## Related pages
- [Pipeline-Architecture](Pipeline-Architecture.md) — the overall architecture and per-source shape that this runbook operates
- [Data-Contracts](Data-Contracts.md) — what pandera and dbt enforce at each boundary; what failures look like at the validation layer

## Relevance to current work
Any new source added via `/add-source` must: add its mart table(s) to
`validate_marts_task`'s `mart_tables` list in `tasks.py`, otherwise `make pipeline`
will complete without verifying the new star's row counts. The step order (seed before
run, snapshot before run) must be respected — new seed-backed dimensions follow the
same pattern as `dim_admission_type` and `dim_severity`.

_Last reviewed: 2026-07-26_
