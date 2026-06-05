# Phase 2 — Diabetes readmission as a second fact table

**Status:** in progress (branch `feat/phase2-diabetes-fact-table`, stacked on `feat/incremental-scd2-historization`).
**Goal:** make the "multi-source clinical ETL pipeline" claim real by wiring the UCI
*Diabetes 130-US hospitals* dataset (`data/raw/diabetes_readmission/diabetic_data.csv`)
through the full pipeline as a second, independent star schema — proving the architecture
generalizes beyond the single `claims_fraud` source.

## The data (profiled, not assumed)

- **101,766 rows × 50 columns**, one CSV (no Train/Test split, unlike claims).
- **Grain:** `encounter_id` — verified unique → natural key for the fact table.
- **Patient:** `patient_nbr` — 71,518 distinct (a patient can have many encounters) → dimension key.
- **Missing sentinel is the string `?`** (not blank/NaN): `weight` 96.9%, `medical_specialty`
  49.1%, `payer_code` 39.6%, `race` 2.2%, `diag_3` 1.4%, `diag_2` 0.4%, `diag_1` 0.02%.
  Must be recoded `?` → NULL **before** pandera validation so nullable columns pass.
- **Outcome:** `readmitted` ∈ {`NO`, `>30`, `<30`}. Analytical target = readmitted within 30 days
  (`<30`) → derive `is_readmitted_30d` boolean alongside the 3-class `readmitted_status`.
- **23 medication columns** (`metformin`…`metformin-pioglitazone`), values {No, Steady, Up, Down}
  (some are constant `No`). Hyphenated/mixed-case names (`A1Cresult`, `diabetesMed`,
  `glyburide-metformin`) → quoted in SQL, aliased to snake_case in staging.
- **Lookup-id columns:** `admission_type_id` (1–8), `discharge_disposition_id`, `admission_source_id`.
  The source ships an `IDs_mapping` we do not have on disk, but the `admission_type_id`
  mapping is small and well-known → seed a lookup dimension from it.

## Target model — a second star (mirrors the claims star)

```
dim_patient (grain: patient_nbr)        dim_admission_type (seed lookup)
        │ patient_nbr                              │ admission_type_id
        └───────────┬──────────────────────────────┘
                fct_encounters (grain: encounter_id, incremental)
```

- **`fct_encounters`** (mart, `materialized=incremental`, `unique_key=encounter_id`,
  `delete+insert`) — extends the incremental story to the second fact. Measures
  (time_in_hospital, num_lab_procedures, num_procedures, num_medications, number_outpatient/
  emergency/inpatient, number_diagnoses, derived `num_prior_visits`, `num_diabetes_meds`),
  degenerate dims (admission/discharge/source ids, medical_specialty, age_bracket, diag_1/2/3,
  max_glu_serum, a1c_result, insulin, metformin), and the outcome (`readmitted_status`,
  `is_readmitted_30d`). FK `patient_nbr` → dim_patient, `admission_type_id` → dim_admission_type.
- **`dim_patient`** (mart, table) — one row per patient: race, gender (from latest encounter
  via `DISTINCT ON`), plus aggregates `total_encounters`, `num_readmissions_30d`,
  `readmission_30d_rate`.
- **`dim_admission_type`** (mart, table from a **dbt seed** — exercises the empty `seeds/` dir)
  — admission_type_id → label (Emergency, Urgent, Elective, …).

## Sequenced build (each step is one commit)

1. **Ingestion** — `DiabetesEncounterSchema` (pandera) in `schemas.py`; `clean_diabetes_frame`
   (`?`→NA, unit-testable, no DB) + `load_diabetes_encounters` in `loaders.py`; register
   `diabetes_encounters` natural key; call from `run_ingestion()` and `reset_raw_tables()`.
   *Touches:* `ingestion/schemas.py`, `ingestion/loaders.py`.
2. **dbt staging + source** — `stg_diabetes_encounters.sql` (recode, cast, snake_case, derive
   outcome flags); add `diabetes_encounters` table to the existing `raw` source in
   `src_raw.yml`; staging `schema.yml` tests (unique encounter_id, not_null patient_nbr,
   accepted_values readmitted_status/gender).
3. **dbt intermediate + marts** — `int_encounters_enriched.sql` (view, derived fields);
   `fct_encounters.sql` (incremental); `dim_patient.sql` (table); `admission_type_mapping.csv`
   seed + `dim_admission_type.sql`; marts `schema.yml` (tests + column docs); a singular test
   `assert_readmitted_flag_consistent.sql` (is_readmitted_30d ⇔ readmitted_status='<30').
4. **pytest** — `test_diabetes_schema.py` (valid row, `?`-recode, bad readmitted rejected,
   encounter_id uniqueness) + `clean_diabetes_frame` unit test.
5. **Orchestration + Makefile** — `dbt_seed_task` run before `dbt_run` in the flow;
   `validate_marts_task` includes `fct_encounters`/`dim_patient`; README/Makefile notes.
6. **Docs** — README (Roadmap: Phase 2 done; second star ERD/lineage), `CLAUDE.md`
   (multi-source now real), `BACKLOG.md` (check off diabetes), `docs/data-sources.md`,
   source descriptions; session log under `docs/session-logs/`.
7. **Verify end-to-end** — `make pipeline` (both datasets idempotent), `pytest`, `dbt run` +
   `dbt test` green, mart row counts, re-run no-op. Then commit sequence + stacked PR.

## Design decisions (and why)

- **Second independent star, not a forced join.** Diabetes shares no key with Medicare claims;
  inventing a synthetic bridge would be dishonest. Multi-source ≠ one-warehouse-of-everything —
  it means the pipeline ingests/validates/models heterogeneous sources through the same patterns.
- **Reuse, don't refactor.** The diabetes path is added *alongside* the claims `TABLE_CONFIG`
  loop (single-CSV, no train/test merge) — existing behavior and tests stay intact (small blast
  radius). Same `load_to_postgres` upsert loader, same `validate()` reject-quarantine, same
  staging→intermediate→marts layering.
- **`fct_encounters` is incremental too.** Keeps the production-shaping story consistent across
  both facts; `int_encounters_enriched` stays a view (parallels `int_claims_*`).
- **Seed-backed `dim_admission_type`.** Turns an opaque integer into a labeled conformed
  dimension and finally uses `dbt/seeds/` — a clean dimensional-modeling signal.
- **Honest framing.** Single-vintage data (1999–2008), so no real CDC; readmission risk is
  descriptive feature engineering, not a deployed model — stated as such in docs.
