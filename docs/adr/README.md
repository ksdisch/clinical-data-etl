# Architecture Decision Records

Numbered records of the load-bearing decisions in this pipeline — the "why did you do it
this way?" answers, in a form you can skim. Each record is immutable once **Accepted**; when a
decision changes we add a new ADR and mark the old one **Superseded** (with a pointer), rather
than editing history.

These ADRs distil and structure the narrative in
[`PROJECT_GUIDE.md` § "Decisions & Tradeoffs"](../../PROJECT_GUIDE.md) and the "Architectural
Decisions" section of [`CLAUDE.md`](../../CLAUDE.md). Where they overlap, the ADR is the
authoritative, discrete record.

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-etl-not-ml-merge-train-test.md) | Merge Train/Test splits at ingest (ETL, not ML) | Accepted |
| [002](002-fraud-label-in-dim-provider.md) | Keep the fraud label in `dim_provider`, not on `fct_claims` | Accepted |
| [003](003-reject-and-continue-validation.md) | Reject-and-continue validation; orphan claims as a warn | Accepted |
| [004](004-three-independent-stars.md) | Model three independent stars, no conformed cross-source key | Accepted |
| [005](005-idempotent-upsert-loader.md) | Idempotent `ON CONFLICT` upsert loader with first-seen `ingested_at` | Accepted (supersedes the DROP CASCADE reload) |
| [006](006-incremental-boundary-not-exists.md) | Incremental boundary via `NOT EXISTS` set-membership anti-join | Accepted |
| [007](007-scd2-fraud-history-snapshot.md) | SCD2 fraud-label history via a dbt snapshot | Accepted |
| [008](008-minted-surrogate-admission-id.md) | Mint a surrogate `admission_id` for the keyless hospital source | Accepted |
| [009](009-subprocess-dbt-invocation.md) | Invoke dbt via subprocess, not the Python API | Accepted |
| [010](010-seed-backed-conformed-lookups.md) | Seed-backed conformed lookup dimensions | Accepted |

## Convention

- **File:** `docs/adr/NNN-short-slug.md`, `NNN` zero-padded to 3 digits.
- **Title:** `ADR-NNN: Title Case`.
- **Sections:** Context · Decision · Consequences · Status.
- **Status values:** `Accepted` · `Superseded by ADR-NNN` · `Deprecated`.
- Start a new record from [`000-template.md`](000-template.md).
