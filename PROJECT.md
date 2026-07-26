# PROJECT.md

## Purpose
A portfolio project for Data Engineering / Analytics Engineering roles: a multi-source clinical data ETL pipeline that ingests three heterogeneous Kaggle healthcare datasets, validates them with pandera, stages into PostgreSQL, transforms with dbt into three independent star schemas, and orchestrates with Prefect.

## Scope
**In scope (current phase):**
- Three wired sources: Medicare claims fraud (4 tables), UCI diabetes readmission (101,766 encounters), synthetic hospital admissions (5,000 rows)
- Idempotent `ON CONFLICT` upsert ingestion, incremental dbt models (`NOT EXISTS` hash anti-join boundary), SCD2 fraud-label history
- Engineering documentation: ADRs (`docs/adr/`), data dictionary, data-sources reference, phase plans

**Out / deferred / never:**
- Deferred: static dbt-lineage PNG for the README (needs a running DB; see BACKLOG.md)
- Never (by design): ML modeling — this is ETL, so Train/Test splits are merged at ingest (ADR-001); no conformed key joining the three stars (ADR-004)

## Current status
Active (between milestones). MVP + production-shaping (incremental/SCD2) + Phase 2 (diabetes star) + Phase 3 (hospital star) + Tier 3 docs are all complete; `make pipeline` runs all three sources end-to-end idempotently (~1 min re-run); 56 pytest tests and 98 dbt tests (97 pass, 1 expected warn). BACKLOG.md has nothing open; the docs roadmap (`docs/artifacts-plan.md`) is drained except the deferred lineage screenshot.

## Next actions
1. (Deferred, optional) Capture the static dbt-lineage screenshot for the README — requires a running Postgres + `make dbt-docs`
2. Decide the next milestone (no open backlog items) — e.g. via `/brainstorm` or `/autonomous-milestone` triage

## Boundaries
- Tech: Python 3.11+, PostgreSQL 16 via Docker (local port 5433), dbt-core/dbt-postgres pinned `>=1.10,<1.11` (incremental/snapshot APIs are version-sensitive), Prefect 2.x with repo-scoped `PREFECT_HOME`
- Data access: raw data is gitignored; downloading requires Kaggle CLI credentials (`~/.kaggle/kaggle.json`)
- Data limits: all three sources are single-vintage, so incrementality and SCD2 are demonstrated with deterministic seeded demos (`make demo-incremental`, `make demo-scd2`) — framed honestly as demos, not real CDC
- Modeling constraints: fraud label stays in `dim_provider` (ADR-002); hospital source has no usable natural PK, so `admission_id = md5(case_id-patientid)` is minted at ingest (ADR-008)
