# ADR-008: Mint a surrogate `admission_id` for the keyless hospital source

**Status:** Accepted

## Context

The tertiary synthetic-hospital dataset has **no usable primary key**. Its `case_id` looks like an
identifier but is **recycled across unrelated admissions** — the same `case_id` appears on rows that
are clearly different admissions. The only combination that is unique in the source is the
`(case_id, patientid)` pair. A fact table needs a stable, unique grain key; using `case_id` alone would
collapse distinct admissions, and exposing a composite `(case_id, patientid)` key through every
downstream join is awkward and easy to get wrong.

## Decision

Mint a deterministic surrogate at ingestion: `admission_id = md5(case_id-patientid)`, computed in
`clean_hospital_frame` **before** pandera validation, and declared `unique=True` in
`HospitalAdmissionSchema`. `admission_id` becomes the grain of `fct_hospital_admissions` and its
`unique_key` for incremental loading. The original `case_id` is retained as a **degenerate dimension**
on the fact (it carries no clean functional dependency to a separate dimension table).

Because the surrogate is a pure hash of the business key, it is **deterministic and idempotent** — re-
ingesting the same admission produces the same `admission_id`, which is exactly what the `ON CONFLICT`
upsert (ADR-005) and the `NOT EXISTS` incremental boundary (ADR-006) require.

## Consequences

- **Easier:** a single, stable, unique grain key for the hospital star; clean joins to
  `dim_hospital_patient`; idempotent re-ingest.
- **Harder / accepted:** the surrogate is opaque (an md5 hash, not human-readable) and is minted in the
  ingestion layer rather than the source — anyone tracing a row back to the CSV must reconstruct it from
  `(case_id, patientid)`. The recode and minting are documented in `schemas.py`, the data dictionary, and
  `CLAUDE.md`. The same source's `20-Nov` → `11-20` Excel-corruption recode is handled in the same
  `clean_hospital_frame` step.
