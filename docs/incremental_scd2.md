# Incremental loading, idempotent backfills & SCD2 history

This document explains the "production-shape the warehouse" milestone: how the
pipeline moved from a naive full DROP+reload to **incremental** dbt models with a
**provably idempotent** load path, and how it tracks **SCD Type 2** history on the
provider fraud label.

## Why

The original pipeline dropped and fully reloaded every table on each run
(`DROP TABLE ... CASCADE` + `to_sql append`). That's the clearest "tutorial, never
run in production" tell. This milestone replaces it with the two mechanics every
analytics-engineering interview probes — incremental materializations and SCD2
snapshots — while keeping the default `make pipeline` output identical.

## 1. Idempotent upsert loader

`load_to_postgres` (`src/clinical_data_etl/ingestion/loaders.py`) no longer drops
anything. It:

1. creates the target table from the DataFrame shape if absent,
2. ensures a `UNIQUE INDEX` on the natural key (`BeneID` / `ClaimID` / `Provider`),
3. loads the batch into a session staging table, then
4. `INSERT ... SELECT ... ON CONFLICT (key) DO UPDATE` merges it in.

An `ingested_at` audit column is stamped on first insert and **never overwritten**
on conflict, so re-loading identical data is a true no-op. `mode="replace"`
(TRUNCATE, not DROP) is available for a clean rebuild — it preserves the dependent
dbt views and the DB-resident snapshots, unlike the old `DROP ... CASCADE`.

Because raw tables are never dropped, the dbt staging **views** survive ingestion
(the old CASCADE used to tear them down), so re-runs no longer leave the warehouse
in a half-built state.

## 2. Incremental models — and the aggregate boundary

`int_claims_enriched` and `fct_claims` are `materialized='incremental'`
(`unique_key='claim_id'`, `incremental_strategy='delete+insert'`).

**The boundary is deliberate.** `int_claims_unified` stays a **full view** because
`dim_provider` aggregates over it (`count/sum/avg/count(distinct)` grouped by
provider). If that model were incremental, the provider aggregates would silently
undercount on every incremental run. Keeping it full — and making only the
downstream `int_claims_enriched → fct_claims` path incremental — means every
aggregation still reads a complete relation. (`int_claims_enriched` is consumed
only by `fct_claims`, so making it incremental is safe.) A fitness check asserts
`sum(dim_provider.total_claims) == count(fct_claims) == 693,603`.

The incremental predicate is `where claim_id not in (select claim_id from {{ this }})`.

## 3. Honest note on the "delta": this is a seeded demo

The Medicare dataset is single-vintage (claims cluster in ~2009) and the Train/Test
split is by **provider**, not by time — there is **no natural time delta or
late-arriving stream**. So incrementality and SCD2 change-history are demonstrated
with **deterministic, seeded** inputs, not by pretending the source data changes on
its own:

- **`make demo-incremental`** partitions claims into two stable hash buckets of
  `claim_id`, loads bucket 0 + full-refresh, then loads bucket 1 + an incremental
  run, and asserts the incremental run inserted *exactly* the bucket-1 claims (no
  duplicates), reached the full row count, and that a second run is a no-op.
- **`make demo-scd2`** flips `is_potential_fraud` from `No → Yes` on a fixed set of
  providers, re-snapshots, and asserts a second version row materialises with
  correct validity (old row closed, new row current). It restores the baseline at
  the end, so it is re-runnable.

This is called out explicitly because faking change-data to demo change-data-capture,
*unlabelled*, would be the wrong signal. The machinery is real; the trigger is seeded.

## 4. SCD2 history on the fraud label

`dbt/snapshots/snap_provider_fraud.sql` is a `check`-strategy snapshot keyed on
`provider_id` over `is_potential_fraud`, reading `source('raw','providers')`
directly (so it's decoupled from the model DAG and can run before `dbt run`). The
`dim_provider_history` mart exposes `valid_from` / `valid_to` / `is_current`,
answering "when did this provider's fraud flag change?".

Two singular tests enforce temporal validity:
`assert_provider_history_no_overlap` (no overlapping windows per provider) and
`assert_provider_history_one_current` (exactly one open row per provider).

## Commands

| Command | What it does |
|---|---|
| `make pipeline` | Idempotent run: upsert ingest → snapshot → incremental dbt run → test → validate |
| `make pipeline-reset` | Clean rebuild: TRUNCATE raw (snapshots survive) + `dbt run --full-refresh` |
| `make demo-incremental` | Self-verifying proof of incremental adds + idempotency |
| `make demo-scd2` | Self-verifying proof of SCD2 history (seeded second vintage) |

## Verified fitness functions (local)

- Default & reset pipelines: `fct_claims` 693,603; `dim_provider_history` 6,763.
- `dim_provider` aggregate reads the full relation (no undercount).
- `make demo-incremental`: 5/5 checks pass.
- `make demo-scd2`: 4/4 checks pass, baseline restored.
- dbt test: PASS=45 / WARN=1 (expected 88-orphan relationship) / ERROR=0.
- pytest: 39 passed; `mypy --strict` and `ruff` clean.
