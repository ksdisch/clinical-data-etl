# Backlog

Lightweight fix-tracking for clinical-data-etl — open items so they don't get lost.
This is not a sprint board. For the documentation roadmap, see [`docs/artifacts-plan.md`](docs/artifacts-plan.md).

## Open

_Nothing open._

## Deferred
- [ ] **dbt lineage screenshot.** `make dbt-docs` renders the DAG, but capturing a static
  `docs/images/dbt-lineage.png` for the README needs a running DB (Tier 2 #8 in `docs/artifacts-plan.md`).

## Recently done
- [x] **Tier 3 docs.** Added a numbered ADR directory (`docs/adr/`, 10 records + index + template)
  capturing the load-bearing decisions, a column-level `docs/data-dictionary.md` covering all three
  stars (raw → staging rename → mart), and full column descriptions for the four intermediate models in
  `dbt/models/intermediate/schema.yml`. Docs-only — no SQL/source behaviour changed. See
  [`docs/phase5-tier3-docs-plan.md`](docs/phase5-tier3-docs-plan.md).
- [x] **Tertiary source — synthetic hospital admissions.** Wired `amulyas/synthetic-hospital-data`
  (5,000 admissions) as a third, independent star: `HospitalAdmissionSchema` (mints a surrogate
  `admission_id` because `case_id` is recycled; recodes the Excel `20-Nov`→`11-20` artifact),
  `stg_hospital_admissions` → `int_admissions_enriched` → `fct_hospital_admissions` (incremental) +
  `dim_hospital_patient` + seed-backed `dim_severity`. See [`docs/phase3-hospital-plan.md`](docs/phase3-hospital-plan.md).
- [x] **Incremental re-run perf.** Switched the four incremental models' boundary from `NOT IN` to
  `NOT EXISTS` (hash anti-join) — a full `make pipeline` re-run dropped from a >14-min hang to ~59s.
- [x] **Phase 2 second source — diabetes readmission.** Wired `brandao/diabetes` (101,766 encounters)
  through the full pipeline as a second, independent star: `DiabetesEncounterSchema` (`?`→NA),
  `stg_diabetes_encounters` → `int_encounters_enriched` → `fct_encounters` (incremental) +
  `dim_patient` + seed-backed `dim_admission_type`. See [`docs/phase2-diabetes-plan.md`](docs/phase2-diabetes-plan.md).
- [x] **Prefect local DB conflict.** `Makefile` now scopes `PREFECT_HOME := $(CURDIR)/.prefect`
  (gitignored) so a shared `~/.prefect/prefect.db` from another project can't break flow runs.
- [x] **Pin dependencies / commit a lockfile.** `dbt-core`/`dbt-postgres` pinned to `>=1.10,<1.11`
  (incremental/snapshot APIs are version-sensitive) and `uv.lock` is now committed.
- [x] **Add a dbt job to CI.** `.github/workflows/ci.yml` has a `dbt` job that runs `dbt compile`
  against a Postgres service — validates models, incremental configs, the snapshot, and custom
  tests without needing Kaggle data.
- [x] **Incremental + SCD2 milestone.** Replaced full DROP+reload with an idempotent ON CONFLICT
  upsert loader, incremental `int_claims_enriched`/`fct_claims`, and SCD2 history on the fraud
  label (`snap_provider_fraud` → `dim_provider_history`). See [`docs/incremental_scd2.md`](docs/incremental_scd2.md).

---

_The dbt 1.7 → 1.10 floor bump (commit `aab50d4`) is complete._
