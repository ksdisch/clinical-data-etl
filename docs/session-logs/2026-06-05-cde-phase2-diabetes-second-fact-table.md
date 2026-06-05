# Session log — clinical-data-etl — Phase 2: diabetes second fact table

**Date:** 2026-06-05
**Branch:** `feat/phase2-diabetes-fact-table` (stacked on the unmerged
`feat/incremental-scd2-historization`).
**Outcome:** the UCI diabetes-readmission dataset is wired end-to-end as a
second, independent star schema. Multi-source is now real, not aspirational.

---

## 1. What we did

- Ran an `/autonomous-milestone` triage (5 cheap parallel agents) over the backlog;
  chose **Phase 2 — diabetes as a second fact table** from a ranked slate.
- Profiled the data first (not assumed): 101,766 rows, grain `encounter_id`
  (unique), patient `patient_nbr` (71,518), `?` missing sentinel, `readmitted` ∈
  {NO, >30, <30}, 23 medication columns.
- **Ingestion:** `DiabetesEncounterSchema` (pandera) + `clean_diabetes_frame`
  (`?`→NA, DB-free/unit-testable) + `load_diabetes` (single CSV, no train/test
  merge). Reused the existing `load_to_postgres` ON CONFLICT upsert with
  `key='encounter_id'`; folded into `run_ingestion` and `reset_raw_tables`.
- **dbt (second star):** `stg_diabetes_encounters` → `int_encounters_enriched`
  (view; derives `num_prior_visits`, `num_diabetes_meds`) → `fct_encounters`
  (incremental, `unique_key='encounter_id'`) + `dim_patient` (table) +
  `dim_admission_type` (first use of `dbt/seeds/`). Added a singular test
  asserting `is_readmitted_30d ⇔ readmitted_status='<30'`.
- **Orchestration:** new `dbt_seed_task` (step 2/6, before run);
  `validate_marts_task` now covers both stars.
- **Tests:** 7 new schema tests + a seed-task test; updated the dual-source
  integration test and its skip-guard. **47 pytest** + **71 dbt** tests
  (70 pass, 1 expected warn) green.
- **Verified by running**, not inspection: all 101,766 rows validate with 0
  rejects; incremental re-run is `INSERT 0`; overall 30-day readmission rate
  **11.16%** (matches published figures for this dataset).

---

## 2. The why

- **Two independent stars, no forced join.** Diabetes and Medicare claims share
  no key. Inventing a synthetic bridge would be dishonest; multi-source means the
  *same patterns* ingest/validate/model *heterogeneous* sources — not one
  warehouse-of-everything. So `fct_encounters`/`dim_patient` stand alone.
- **Recode `?`→NA before validation.** The UCI CSV encodes missing categoricals
  as the literal string `?`. pandera's `nullable` only recognises NA/NaN, so the
  recode must precede `.validate()`. Kept it in a pure helper (`clean_diabetes_frame`)
  so it is unit-testable without a database.
- **Reuse, don't refactor.** Added the single-CSV diabetes path *alongside* the
  claims `TABLE_CONFIG` loop instead of generalising the loader — small blast
  radius, existing claims behaviour and tests untouched.
- **`fct_encounters` incremental too.** Keeps the production-shaping story
  consistent across both facts; `int_encounters_enriched` stays a view, mirroring
  `int_claims_*`.
- **Seed-backed `dim_admission_type`.** Turns the opaque `admission_type_id`
  integer into a labelled conformed dimension and finally exercises the empty
  `dbt/seeds/` dir — a clean dimensional-modelling signal. This is why the flow
  gained a `dbt seed` step (and the flow tests gained a patch for it).
- **The flow-test failures were the Prefect DB gotcha, not the code.** Running
  `pytest` directly hit the corrupted shared `~/.prefect/prefect.db`
  (`alembic … Can't locate revision`). With `PREFECT_HOME` scoped to the project
  (as the Makefile already does), all 12 passed. Principle from last session held:
  isolate, don't mutate shared/foreign state.

---

## 3. Concepts and vocabulary

- **Conformed / lookup dimension** — a small reference table (here from a dbt
  seed) that labels a code (`admission_type_id` → Emergency/Urgent/…).
- **dbt seed** — a CSV checked into `seeds/` that dbt loads as a table; good for
  small static reference data.
- **Degenerate dimension** — a dimensional attribute stored on the fact with no
  separate dimension table (e.g. `diag_1`, `discharge_disposition_id`).
- **Grain** — the one-row-per-X definition of a fact. Here: one hospital encounter.
- **Missing sentinel** — a non-null placeholder for missing data (`?`), recoded
  to true NULL at ingestion.
- **`DISTINCT ON` (Postgres)** — picks one row per group; used to take each
  patient's latest-encounter demographics for `dim_patient`.
- **Incremental model / `delete+insert`** — dbt only processes new keys; re-runs
  are no-ops (`INSERT 0`).

---

## 4. Takeaways

- **Profile before you model.** Confirming `encounter_id` is unique and that `?`
  (not blank) is the sentinel shaped the whole schema — assumptions here would
  have produced silent rejects.
- **Multi-source ≠ one big join.** The honest, stronger story is two clean stars
  sharing infrastructure.
- **Verify by running.** 0 rejects, `INSERT 0` on re-run, and an ~11% readmission
  rate matching the literature are evidence the parser can't give.
- **A skip guard must cover every dependency.** `run_ingestion` now needs both
  sources' CSVs, so `_HAS_RAW_DATA` checks both.

---

## 5. Suggested next moves

1. Merge `feat/incremental-scd2-historization` to `main`, then retarget/merge this PR.
2. **Tertiary source** (synthetic hospital) for a third star, or **Tier 3 docs**
   (ADRs + data dictionary).
3. A small fraud/readmission **analytics mart** on top of the two stars (the
   runner-up milestone) to add the "so what".

---

## 6. 30-second elevator version

I made the "multi-source" claim on my clinical ETL pipeline real. It had only ever
ingested one Medicare-claims dataset; I wired a second, totally different dataset —
100k diabetes hospital encounters — through the same pipeline as its own star
schema. The interesting bits: the data hides missing values behind a literal `?`,
so I recode that to NULL before validation; the two datasets don't share a key, so
I modelled them as two independent stars instead of forcing a join; and I extended
the same incremental + idempotent-upsert patterns to the new fact table, even using
a dbt seed for a labelled admission-type lookup dimension. Everything's verified by
actually running it — 0 validation rejects, idempotent re-runs, and an 11%
readmission rate that matches the published figure.

---

## 7. Active recall

1. Why model diabetes and claims as two independent stars instead of one joined model?
2. Why must `?`→NA happen *before* pandera validation, and why keep it in its own helper?
3. `fct_encounters` is incremental — what does a second `dbt run` print, and why?
4. The flow tests failed under raw `pytest` but passed under `make test`. What was the cause and the fix?
5. What does the `admission_type_mapping` seed buy you over leaving `admission_type_id` on the fact?
