# Phase 3 plan — Tertiary source: synthetic-hospital admissions as a third star

> Status: ✅ complete | Branch: `feat/tertiary-synthetic-hospital-star`
> Milestone selected via `/autonomous-milestone` backlog triage (highest impact/effort/risk).
>
> **Outcome:** third star live (5,000 admissions → `fct_hospital_admissions` + `dim_hospital_patient`
> + `dim_severity`). `make pipeline` green end-to-end across all three sources; re-run is a ~59s no-op
> (after the `NOT IN`→`NOT EXISTS` perf fix that cut a >14-min hang). 56 pytest pass; 98 dbt tests
> (97 pass / 1 expected warn). avg LOS rises with severity (Minor 32 → Moderate 35 → Extreme 39 days).

Wire the tertiary Kaggle dataset (`amulyas/synthetic-hospital-data`,
`data/raw/synthetic_hospital/HospitalSynthetic1.csv`, 5,000 rows × 18 cols) through
the full pipeline as a **third, independent star** — mirroring the path the diabetes
source took (`/add-source` skill). No key joins this star to the claims or diabetes
stars; they stay deliberately independent.

## Why this milestone

Upgrades the narrative from "two-source pipeline" to a **three-source dimensional
warehouse**, proving the ingest → validate → stage → model pattern *generalizes*
(the single strongest DE/AE interview signal beyond "I built a pipeline once"). The
dataset also forces a couple of genuine, defensible data-engineering judgment calls
(below), which is exactly the kind of thing a reviewer probes.

## Source profiling — findings that shaped the design

Profiled `HospitalSynthetic1.csv` before modelling (5,000 rows):

1. **`case_id` is NOT a primary key.** Only 3,601 distinct values; the same
   `case_id` recurs across up to 7 *completely different* admissions (different
   hospital, patient, department, everything). Zero fully-identical duplicate rows.
   → `case_id` is a recycled label, not a grain key.
2. **`Hospital_code` is also recycled.** All 32 codes map to multiple conflicting
   `(type, city, region)` combinations — so there is **no clean source entity** to
   build a conformed "from-source" dimension on (not hospital; `patientid` is ~98%
   unique too). This is a thoroughly randomized synthetic dataset.
3. **`(case_id, patientid)` is unique** across all 5,000 rows — the only usable
   business key.
4. **Excel date-corruption artifact:** the `11-20` bracket is absent from both `Age`
   and `Stay`; in its place is the literal string `20-Nov` (Excel auto-formatted
   "11-20" as a date). Appears in `Age` (244×) and `Stay` (1,270×). Must be recoded
   `20-Nov` → `11-20`.
5. **Nullable columns:** `Bed Grade` (31 nulls), `City_Code_Patient` (121 nulls).
6. **`Stay`** is the dataset's natural analytical target (length-of-stay bracket,
   incl. `More than 100 Days`).

## Design decisions

- **Grain:** one hospital admission (one row).
- **Surrogate key `admission_id`:** since `case_id` is recycled and only
  `(case_id, patientid)` is unique, mint a deterministic content surrogate
  `admission_id = md5(f"{case_id}-{patientid}")` **at ingestion** (Python, pure &
  unit-testable). Single-column → works with the existing `load_to_postgres`
  ON CONFLICT upsert unchanged; stable across re-ingests (idempotent); robust to
  edits in non-key columns. Honest talking point: "the source had no usable PK, so
  I derived a deterministic surrogate from the unique business key."
- **`20-Nov` → `11-20` recode** lives in a pure `clean_hospital_frame(df)` (mirrors
  `clean_diabetes_frame`'s `?`→NA recode) so it is testable and runs *before* pandera.
- **Analytical target:** length of stay. Derive `length_of_stay_days` (bracket
  midpoint) and `is_long_stay` (`> 30` days, ~48% of rows) — the binary target
  mirrors diabetes' `is_readmitted_30d`. Framed as descriptive feature engineering
  on a single synthetic vintage (not a deployed model), same as the diabetes star.
- **Star shape mirrors diabetes** (fct + source-aggregate dim + seed-backed dim):
  - `fct_hospital_admissions` — incremental fact, grain `admission_id`; degenerate
    dimensions (hospital/ward/department codes, since no clean FD) + measures.
  - `dim_hospital_patient` — behavioral rollup per `patientid` (total_admissions,
    avg_length_of_stay_days, total_admission_deposit, distinct_hospitals). Most
    patients appear once; the dim surfaces the small repeat-admission cohort.
  - `dim_severity` — seed-backed conformed lookup mapping `Severity of Illness`
    (Minor/Moderate/Extreme) → ordinal `severity_rank` (1/2/3) + description.

## File-by-file plan

### Ingestion (`src/clinical_data_etl/ingestion/`)
- `schemas.py`: add `HospitalAdmissionSchema` (source column names incl. spaces, +
  `admission_id` unique non-null; `Bed Grade`/`City_Code_Patient` nullable; `isin`
  enums for coded categoricals; `Age`/`Stay` brackets incl. recoded `11-20`).
- `loaders.py`: `HOSPITAL_DATA_DIR/_CSV_GLOB/_TABLE` consts;
  `NATURAL_KEYS["hospital_admissions"]="admission_id"`; pure `clean_hospital_frame`
  (recode + mint surrogate) + `load_hospital`; processing block in `run_ingestion`;
  add to `reset_raw_tables`.

### dbt (`dbt/`)
- `models/staging/src_raw.yml`: declare `hospital_admissions` source.
- `models/staging/stg_hospital_admissions.sql` (view): snake_case rename, surface key.
- `models/intermediate/int_admissions_enriched.sql` (view): `length_of_stay_days`,
  `is_long_stay`.
- `models/marts/fct_hospital_admissions.sql` (incremental, `unique_key=admission_id`,
  `delete+insert`, `on_schema_change=sync_all_columns`).
- `models/marts/dim_hospital_patient.sql` (table) + `dim_severity.sql` (table).
- `seeds/severity_mapping.csv` (severity_of_illness, severity_rank, severity_description).
- `schema.yml` entries (staging/intermediate/marts) with unique/not_null/
  accepted_values/relationships tests; singular tests
  `assert_length_of_stay_non_negative.sql` + `assert_long_stay_flag_consistent.sql`.

### Orchestration / tests
- `orchestration/tasks.py`: add the 3 hospital marts to `validate_marts_task`.
- `tests/test_ingestion/test_hospital_schema.py`: schema valid/reject, recode,
  surrogate uniqueness+stability.
- `tests/test_ingestion/test_loaders.py`: extend `_HAS_RAW_DATA` + the integration
  test's expected key set with `hospital_admissions`.

### Infra / docs
- `docker-compose.yml`: host port honors `POSTGRES_PORT` (default 5432) — groundwork
  so local verification works where 5432 is taken (done).
- README (architecture, 3rd ERD, lineage mermaid, roadmap), CLAUDE.md (data sources,
  architecture, current priority), `docs/data-sources.md`, `BACKLOG.md` (tertiary →
  done).

## Verification (definition of done)
- `make pipeline` green end-to-end across **three** sources; **re-run is a no-op**.
- `pytest` all pass (incl. new hospital tests + updated integration test).
- `dbt test` all pass (1 pre-existing expected warn on orphan claims relationship).
- 3 new marts populated; `admission_id` unique on the fact; `is_long_stay` consistent.
- Open PR; **do not merge to main**.
