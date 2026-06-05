---
name: add-source
description: >
  Wire a brand-new raw data source into the clinical-data-etl pipeline end to
  end — pandera schema, ingestion loader (idempotent upsert with a first-seen
  ingested_at and sentinel→NA recode), raw table, dbt staging model, and (for a
  new analytical subject) an independent star. Use when adding a dataset such as
  the tertiary synthetic-hospital source, or when the user says "/add-source"
  or "ingest a new dataset". Follows the path the diabetes source took.
---

# add-source

Add a new source the way the **diabetes** secondary source was added. Read the
existing diabetes path first — it is the reference implementation:

- `src/clinical_data_etl/ingestion/schemas.py` → `DiabetesEncounterSchema`
- `src/clinical_data_etl/ingestion/loaders.py` → `clean_diabetes_frame`,
  `load_diabetes`, `NATURAL_KEYS`, `load_to_postgres`, `run_ingestion`
- `dbt/models/staging/stg_diabetes_encounters.sql` (+ `src_raw.yml`, `schema.yml`)
- `dbt/models/marts/{fct_encounters,dim_patient,dim_admission_type}.sql`

## Step 0 — Clarify the source

- **Files & layout**: where under `data/raw/<source>/`? Single CSV (like diabetes)
  or a Train/Test split to merge (like claims)?
- **Grain / natural key**: the column that uniquely identifies a row — backs the
  `ON CONFLICT` upsert.
- **Missing-value sentinel**: does it use a literal like `?`, `N/A`, `-1`? It must
  be recoded to `pd.NA` *before* pandera validation (pandera's `nullable` only sees
  NA/NaN).
- **New star or extend existing?** A genuinely new subject → its own independent
  star (no key joining it to the claims or diabetes stars).

## Step 1 — pandera schema (`ingestion/schemas.py`)

Add `<Source>Schema = DataFrameSchema(columns={...}, coerce=True)`. Match the
existing style: `Column(<type>, <pa.Check...>, nullable=...)`, `unique=True` on the
natural key, helper functions for repeated column groups. Use `pa.Check.ge(0)` for
non-negative amounts, `pa.Check.isin([...])` for enums.

## Step 2 — Loader wiring (`ingestion/loaders.py`)

1. Register the natural key in `NATURAL_KEYS[<table>] = "<key_col>"`.
2. If single-CSV: add a `load_<source>()` (mirror `load_diabetes`) and, if there's a
   sentinel, a pure `clean_<source>_frame(df)` (mirror `clean_diabetes_frame`) so it
   is unit-testable. If Train/Test: add an entry to `TABLE_CONFIG` instead.
3. Load with the shared idempotent upsert — **do not** write a bespoke loader:

   ```python
   valid_df, rejected_df = validate(df, <Source>Schema, "<table>")
   load_to_postgres(valid_df, "<table>", mode=mode, ingested_at=ingested_at)
   ```

   `load_to_postgres` handles `CREATE SCHEMA`, table/unique-index creation,
   `INSERT ... ON CONFLICT (key) DO UPDATE`, and stamps `ingested_at` once
   (never overwritten — so a re-run is a no-op). Pass the shared `ingested_at`.
4. Add a processing block to `run_ingestion()` and include the table in
   `reset_raw_tables()` so `make pipeline-reset` truncates it too.

## Step 3 — dbt staging

- Declare the raw table in `dbt/models/staging/src_raw.yml` under `source('raw', ...)`.
- Add `dbt/models/staging/stg_<source>.sql`: clean column names → snake_case, cast
  types, recode coded values, surface the natural key. Add a `schema.yml` entry with
  `unique` + `not_null` on the key. (See the [[new-dbt-model]] skill for the
  schema.yml test conventions — `arguments:` block form.)

## Step 4 — Star (if a new subject)

Build the star with the [[new-dbt-model]] skill: an intermediate enrichment view →
an incremental `fct_<grain>` (the `delete+insert` / `is_incremental()` pattern) +
`dim_*` tables. Seed-backed lookups go in `dbt/seeds/` (e.g.
`admission_type_mapping.csv`) and load via `dbt seed`. Keep the new star independent.

## Step 5 — Tests

- pytest in `tests/test_ingestion/`: the pandera schema (valid + rejecting bad rows),
  the sentinel recode (`clean_<source>_frame`), and that ingestion loads the source.
  Use sample-DataFrame fixtures.
- dbt schema tests on the new staging/mart models.

## Step 6 — Verify & document

```bash
make pipeline           # idempotent end-to-end; re-run must be a no-op
make test               # pytest
.venv/bin/dbt test --profiles-dir dbt --project-dir dbt
```

Update `CLAUDE.md` (Data Sources + Architecture), `docs/data-sources.md`, and
`BACKLOG.md`. Commit in focused steps per the repo's conventional-commit style.
