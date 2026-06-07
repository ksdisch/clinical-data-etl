# ADR-006: Incremental boundary via `NOT EXISTS` set-membership anti-join

**Status:** Accepted

## Context

`fct_claims` and `int_claims_enriched` are materialised `incremental` so that re-runs process only new
rows. The usual incremental boundary is a timestamp high-water mark (`where updated_at > max(updated_at)`).
This data has **no usable time delta** — it is a single ~2009 vintage, so every row has effectively the
same date. The honest "new rows only" predicate is therefore **set-membership on the key**: process only
claims whose `claim_id` is not already materialised in the target.

A first implementation expressed this as `claim_id NOT IN (select claim_id from {{ this }})`. Over
~693k claims, Postgres planned that as a correlated per-row subplan and a full `make pipeline` re-run
hung for >14 minutes.

## Decision

Express the boundary as a `NOT EXISTS` correlated anti-join instead of `NOT IN`:

```sql
{% if is_incremental() %}
where not exists (select 1 from {{ this }} t where t.claim_id = src.claim_id)
{% endif %}
```

Postgres plans this as a single **hash anti-join**, dropping the full re-run from the >14-min hang to
~59s. A second decision pairs with this: `int_claims_unified` stays a **full view** (not incremental)
because `dim_provider` aggregates over the complete claim set — only `int_claims_enriched` and
`fct_claims` are incremental, with `unique_key='claim_id'` and the `delete+insert` strategy. The same
`NOT EXISTS` pattern is used on `fct_encounters` and `fct_hospital_admissions`.

## Consequences

- **Easier:** idempotent, fast re-runs; the incremental demo (`make demo-incremental`) is a deterministic,
  seeded proof rather than a slow scan.
- **Harder / accepted:** because the boundary is set-membership (not a timestamp), incrementality is
  demonstrated with **deterministic seeded inputs** (hash-bucketed claims), framed honestly as a seeded
  demo of the mechanism, not real change-data-capture. A real time-series source would switch to a
  high-water-mark predicate — its own future ADR.
- **Invariant:** `int_claims_unified` must remain a view; making it incremental would starve the
  `dim_provider` aggregate. This is noted in `CLAUDE.md` and enforced by code review (the
  `dbt-model-reviewer` subagent checks the incremental boundary).
