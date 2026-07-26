# Decisions

Decisions D1–D10 were made before this wiki existed; they are recorded in full as ADRs under `docs/adr/` (linked, not duplicated — the ADR is the source of truth).

| ID | Decision | Status | Date | Source/Rationale |
|----|----------|--------|------|-----------------|
| D1 | Merge Train/Test CSV splits at ingest (this is ETL, not ML) | Approved | pre-2026-07 | [ADR-001](docs/adr/001-etl-not-ml-merge-train-test.md) |
| D2 | Keep the fraud label in `dim_provider`, not denormalized onto `fct_claims` | Approved | pre-2026-07 | [ADR-002](docs/adr/002-fraud-label-in-dim-provider.md) |
| D3 | Reject-and-continue validation; orphan-claims relationship test is a warn | Approved | pre-2026-07 | [ADR-003](docs/adr/003-reject-and-continue-validation.md) |
| D4 | Model three independent stars — no conformed cross-source key | Approved | pre-2026-07 | [ADR-004](docs/adr/004-three-independent-stars.md) |
| D5 | Idempotent `ON CONFLICT` upsert loader with first-seen `ingested_at` (supersedes DROP+reload) | Approved | pre-2026-07 | [ADR-005](docs/adr/005-idempotent-upsert-loader.md) |
| D6 | Incremental boundary via `NOT EXISTS` set-membership anti-join (not `NOT IN`) | Approved | pre-2026-07 | [ADR-006](docs/adr/006-incremental-boundary-not-exists.md) |
| D7 | SCD2 fraud-label history via a dbt snapshot (`snap_provider_fraud` → `dim_provider_history`) | Approved | pre-2026-07 | [ADR-007](docs/adr/007-scd2-fraud-history-snapshot.md) |
| D8 | Mint surrogate `admission_id = md5(case_id-patientid)` for the keyless hospital source | Approved | pre-2026-07 | [ADR-008](docs/adr/008-minted-surrogate-admission-id.md) |
| D9 | Invoke dbt via subprocess from Prefect (not programmatic API) | Approved | pre-2026-07 | [ADR-009](docs/adr/009-subprocess-dbt-invocation.md) |
| D10 | Seed-backed conformed lookup dims (`dim_admission_type`, `dim_severity`) | Approved | pre-2026-07 | [ADR-010](docs/adr/010-seed-backed-conformed-lookups.md) |
| D11 | Initialize the project wiki (PROJECT.md, HANDOFF.md, Sources.md, Decisions.md, Wiki/) with the ADR directory remaining the source of truth for architecture decisions; new decisions get both an ADR (if load-bearing) and a row here | Approved | 2026-07-26 | project-wiki skill INIT run (unattended) |
