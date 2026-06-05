---
name: new-dbt-model
description: >
  Scaffold a new dbt model for the clinical-data-etl project following its
  established conventions — correct layer + prefix (stg_/int_/fct_/dim_),
  a paired schema.yml entry with the right tests, and the incremental config
  pattern this repo actually uses. Use when adding a staging, intermediate, or
  mart model, or when the user says "/new-dbt-model" or "add a dbt model".
---

# new-dbt-model

Scaffold a dbt model that matches this project's conventions exactly. Don't
invent new patterns — mirror the existing models.

## Step 1 — Pin down the model

Ask (or infer from the request):

- **Layer**: `staging` / `intermediate` / `marts`
- **Name + prefix**: `stg_` (staging), `int_` (intermediate), `fct_` (facts) or
  `dim_` (dimensions) in marts. snake_case.
- **Grain**: one row per *what*? (e.g. one row per claim, per encounter, per
  provider). State it explicitly — every fact/dim has a documented grain.
- **Which star** it belongs to: the **claims** star (`fct_claims`, `dim_beneficiary`,
  `dim_provider`) or the **diabetes** star (`fct_encounters`, `dim_patient`,
  `dim_admission_type`). The two stars are deliberately independent — no key joins
  them; do not introduce a cross-star join.

## Step 2 — Place the file

`dbt/models/<layer>/<model_name>.sql`. Read a sibling in the same layer first and
match its style (CTEs, `ref()`/`source()` usage, column ordering).

## Step 3 — Materialization & config

- **staging / intermediate**: default (view). Note: `int_claims_unified` stays a
  **full view on purpose** because `dim_provider` aggregates over it — do not make
  an upstream of an aggregating dimension incremental.
- **facts** (`fct_*`): incremental, using the repo's exact pattern (see
  `dbt/models/marts/fct_claims.sql` and `fct_encounters.sql`):

  ```sql
  {{
      config(
          materialized='incremental',
          unique_key='<grain_key>',
          incremental_strategy='delete+insert',
          on_schema_change='sync_all_columns'
      )
  }}

  select
      <explicit, column-by-column projection>   -- never select *
  from {{ ref('<upstream_intermediate>') }}
  {% if is_incremental() %}
  where <grain_key> not in (select <grain_key> from {{ this }})
  {% endif %}
  ```

- **dimensions** (`dim_*`): `materialized='table'` (or seed-backed like
  `dim_admission_type`).

## Step 4 — Paired schema.yml entry (REQUIRED)

Every model gets a `<layer>/schema.yml` entry — a model with no tests is incomplete
here. Add: a `description:` (state the grain for facts/dims) and per-column tests
following the repo style. Note this project uses the **`arguments:` block form** for
parametrized tests:

```yaml
  - name: <model_name>
    description: >
      One row per <grain>. <what it is / how to join it>.
    columns:
      - name: <grain_key>
        tests: [unique, not_null]          # facts/dims: grain key is unique + not_null
      - name: <fk_column>
        tests:
          - not_null
          - relationships:
              arguments:
                to: ref('<dim_model>')
                field: <fk_column>
      - name: <enum_column>
        tests:
          - accepted_values:
              arguments:
                values: ['A', 'B', 'C']
```

Use `config: { severity: warn }` for a relationship known to have orphans (see the
`bene_id` test on `fct_claims` — 30 beneficiaries are dropped by pandera).

## Step 5 — Architectural guardrails (don't violate)

- The provider **fraud label lives in `dim_provider` only** — never denormalize
  `is_potential_fraud` onto `fct_claims`.
- Keep the grain honest: a join that fans out rows breaks the fact's grain and its
  `unique` test. Verify the join multiplicity.
- Fact projections are **explicit column lists**, not `select *`.

## Step 6 — Verify

From the repo root:

```bash
.venv/bin/dbt parse  --profiles-dir dbt --project-dir dbt   # DB-free: catches parse/ref errors
.venv/bin/dbt run    --profiles-dir dbt --project-dir dbt --select <model_name>+   # needs local DB on :5433
.venv/bin/dbt test   --profiles-dir dbt --project-dir dbt --select <model_name>
```

Then mention the model in `CLAUDE.md` / `docs/` if it changes the documented star shape.
