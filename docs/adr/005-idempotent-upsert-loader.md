# ADR-005: Idempotent `ON CONFLICT` upsert loader with first-seen `ingested_at`

**Status:** Accepted — supersedes the original `DROP TABLE ... CASCADE` reload

## Context

The MVP loader wrote each raw table with `DROP TABLE ... CASCADE` and a full reload. `CASCADE` was
needed because dbt's staging views depend on the raw tables — without it the second pipeline run
errored on the dependency. This worked but had two costs: every run tore down and recreated all
downstream views, and the raw layer had no notion of *when* a row was first seen, so it could not
support the incremental and SCD2 work that the production-shaping milestone required (ADR-006, ADR-007).

## Decision

Replace DROP+reload with an **idempotent upsert**: `load_to_postgres(..., mode='upsert')` issues
`INSERT ... ON CONFLICT (natural_key) DO UPDATE`, ensuring a unique index per natural key first. The
loader stamps a first-seen `ingested_at` that is **never overwritten on conflict** (set only on
insert), so re-ingesting the same row is a true no-op and the first-seen timestamp is stable. A
`mode='replace'` path is retained for clean rebuilds (`make pipeline-reset` truncates raw while
snapshots survive).

## Consequences

- **Easier:** `make pipeline` is fully idempotent — re-running accumulates via `ON CONFLICT` instead of
  rebuilding, downstream views are no longer torn down on every run, and the stable `ingested_at`
  underpins the incremental boundary (ADR-006) and snapshot CDC (ADR-007).
- **Harder / accepted:** the loader must maintain a unique index per natural key and know each table's
  key — slightly more loader logic than a blind reload. Worth it: idempotency is the property that makes
  the rest of the production-shaping milestone possible.
- **Supersedes:** the DROP CASCADE rationale recorded in `PROJECT_GUIDE.md` § "Decisions & Tradeoffs"
  is now historical.
