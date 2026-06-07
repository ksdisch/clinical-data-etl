# ADR-010: Seed-backed conformed lookup dimensions

**Status:** Accepted

## Context

Two stars carry coded categorical columns whose human-readable meaning lives outside the row data. The
diabetes source encodes admission type as an integer `admission_type_id` (1–8) whose labels come from the
UCI data dictionary, not the CSV. The hospital source records `Severity of Illness` as an ordered
category (`Minor` / `Moderate` / `Extreme`) that needs an explicit **ordinal rank** to be sortable and
averageable. This mapping knowledge is small, static, and reference data — it should be version-controlled
and join-able, not hard-coded into a `CASE` expression buried in a model.

## Decision

Express each mapping as a dbt **seed** that builds a conformed lookup dimension:

- `dbt/seeds/admission_type_mapping.csv` → `dim_admission_type` (`admission_type_id` → label), joined by
  `fct_encounters`.
- `dbt/seeds/severity_mapping.csv` → `dim_severity` (`severity_of_illness` → `severity_rank`,
  `severity_description`), joined by `fct_hospital_admissions`.

The seeds are checked into git, loaded by `dbt seed` as the first transform step in `make pipeline`, and
tested (`unique` + `not_null` on the key).

## Consequences

- **Easier:** the reference mappings are version-controlled, diff-reviewable, and tested like any model;
  the ordinal `severity_rank` makes "avg LOS by severity" a clean ordered aggregate (which surfaces the
  monotonic Minor 32 → Moderate 35 → Extreme 39 day trend).
- **Harder / accepted:** seeds are loaded data, so a mapping change requires a `dbt seed` re-run to take
  effect — a deliberate, auditable step rather than a silent code edit. Seeds are the right tool only for
  *small, static* reference data; anything that grows or changes frequently would belong in a source table
  instead.
