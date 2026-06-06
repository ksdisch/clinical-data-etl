# ADR-007: SCD2 fraud-label history via a dbt snapshot

**Status:** Accepted

## Context

A provider's `PotentialFraud` label can change over time (a provider gets flagged, or cleared). The
current-state `dim_provider` (ADR-002) holds only the latest value and cannot answer "what was this
provider's fraud status as of date X?" Capturing that history is a classic slowly-changing-dimension
Type 2 problem. Building SCD2 by hand (effective-dated rows, close-out logic, current-flag maintenance)
is error-prone; dbt ships a snapshot primitive that does exactly this.

## Decision

Use a dbt **snapshot** with the `check` strategy on `is_potential_fraud`:
`dbt/snapshots/snap_provider_fraud.sql` reads `source('raw','providers')` and records a new version
whenever the fraud flag changes. The `dim_provider_history` mart is built from the snapshot — one row
per `(provider_id, validity window)` with `valid_from` / `valid_to` / `is_current`. Two temporal-validity
invariants are enforced by **singular tests** in `dbt/tests/`:

1. no overlapping validity windows for a provider, and
2. exactly one `is_current` row per provider.

Because the source is single-vintage, the history is demonstrated with a **deterministic seeded
fraud-flag flip** (`make demo-scd2`), framed honestly as a seeded demo of the SCD2 mechanism rather
than observed real-world change.

## Consequences

- **Easier:** point-in-time fraud queries become possible; the close-out / current-flag bookkeeping is
  dbt's responsibility, not hand-rolled SQL; the invariants are machine-checked.
- **Harder / accepted:** the snapshot is stateful — it must run (`dbt snapshot`) before the history mart
  on every pipeline run, and it survives `make pipeline-reset` (which truncates raw but not snapshots) so
  accumulated history is not lost on a rebuild. The current-state `dim_provider` and the historical
  `dim_provider_history` must stay consistent in their label semantics.
