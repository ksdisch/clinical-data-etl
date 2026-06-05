# Backlog

Lightweight fix-tracking for clinical-data-etl — open items so they don't get lost.
This is not a sprint board. For the documentation roadmap, see [`docs/artifacts-plan.md`](docs/artifacts-plan.md).

## Open

_Nothing open outside the deferred Phase 2 items below._

## Deferred (until Phase 2 activates)
- [ ] **Tier 3 docs.** ADR directory, full column-level data dictionary, intermediate-model column
  descriptions (see `docs/artifacts-plan.md`).
- [ ] **Phase 2 dataset.** Integrate diabetes readmission (`brandao/diabetes`) as a second fact
  table; the raw-dir placeholder already exists.

## Recently done
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
