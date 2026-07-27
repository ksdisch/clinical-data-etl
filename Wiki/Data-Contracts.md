# Data-Contracts

## Purpose
What each pipeline layer guarantees — and what the next layer assumes. This page
synthesizes the pandera schemas, dbt staging/mart tests, and known quality gaps so
that anyone extending the pipeline knows exactly what invariants hold at each
boundary. No single document covers all three layers together; `docs/data-dictionary.md`
documents raw column types but not the cross-layer guarantees or the known holes.

## Key understanding

### Layer 0 → Layer 1: CSV files → pandera → `raw` schema

**Fact** (from `src/clinical_data_etl/ingestion/schemas.py` and `loaders.py`):

Each source table is validated against its own `DataFrameSchema` with `coerce=True`
(types are coerced before checking). Rows that fail are written to
`data/rejected/<table>_rejected.csv` and the valid remainder continues — this is the
"reject-and-continue" policy (ADR-003). The raw tables therefore contain only
rows that passed pandera.

What pandera enforces per source:

| Source | Key enforcements |
|---|---|
| **Claims: beneficiary** | `BeneID` unique + non-null; `Gender`/`Race` ints; all 11 `ChronicCond_*` columns ∈ {1, 2}; reimbursement floats ≥ 0 |
| **Claims: inpatient_claims** | `ClaimID` unique + non-null; `InscClaimAmtReimbursed` ≥ 0; up to 10 diagnosis + 6 procedure codes (nullable str); `AdmissionDt`/`DischargeDt` non-null |
| **Claims: outpatient_claims** | Same as inpatient minus `AdmissionDt`/`DischargeDt`/`DiagnosisGroupCode` (those columns don't exist in the outpatient CSV) |
| **Claims: providers** | `Provider` unique + non-null; `PotentialFraud` nullable str (Test split has no column → loader adds `NaN` before validation) |
| **Diabetes: encounters** | `encounter_id` unique; `admission_type_id` ∈ [1, 8]; `readmitted` ∈ {NO, >30, <30}; 23 medication columns each ∈ {No, Steady, Up, Down}; `?` sentinel **must be recoded to NA before schema is applied** |
| **Hospital: admissions** | `admission_id` unique (minted surrogate); `Hospital_type_code` ∈ {a…g}; `Hospital_region_code` ∈ {X, Y, Z}; `Type of Admission` ∈ {Emergency, Trauma, Urgent}; `Severity of Illness` ∈ {Minor, Moderate, Extreme}; `Age`/`Stay` must use recoded brackets (`20-Nov` artifact **must be fixed before schema is applied**) |

**Fact** (from `loaders.py` — `_hospital_surrogate_key`, `clean_hospital_frame`,
`clean_diabetes_frame`): The two pre-validation recodes are pure Python functions
applied before any DB write, making them unit-testable and guaranteed to run first.

**Fact** (from `loaders.py` — `load_to_postgres`): Every row loaded to `raw.*` gets an
`ingested_at` audit column stamped at first insert; it is never overwritten on
conflict, so a re-ingest of identical data is a true no-op.

### Layer 1 → Layer 2: `raw` schema → dbt staging (views)

**Fact** (from `dbt/models/staging/schema.yml`): Staging models apply these guarantees:
- Column names are normalized to snake_case.
- Numeric sentinel codes are cast to their semantic types (`Gender`/`Race` int codes
  → human-readable text strings; `ChronicCond_*` 1/2 ints → booleans; `change`/`diabetesMed`
  Yes/No strings → booleans; `is_potential_fraud` Yes/No/NaN → boolean or NULL).
- `claim_duration_days` (`discharge_date − admission_date`) is derived in staging for
  inpatient claims; outpatient rows have it NULL at the `int_claims_unified` union.

**Inference** (from the SQL in `dbt/models/intermediate/int_claims_unified.sql`): The
outpatient-to-inpatient union fills `admission_date`, `discharge_date`,
`claim_duration_days`, and `diagnosis_group_code` with typed NULLs so the union schema
is uniform. Any downstream model that expects those columns non-null must filter on
`claim_type = 'inpatient'`.

### Layer 2 → Layer 3: dbt intermediate → marts

**Fact** (from `dbt/models/marts/schema.yml`): The mart layer adds these dbt schema tests:

| Mart | Uniqueness / not_null | Accepted-values | Relationships |
|---|---|---|---|
| `fct_claims` | `claim_id` unique + not_null | `claim_type` ∈ {inpatient, outpatient} | `bene_id → dim_beneficiary` (**warn**); `provider_id → dim_provider` (**error**) |
| `dim_beneficiary` | `bene_id` unique + not_null | — | — |
| `dim_provider` | `provider_id` unique + not_null | — | — |
| `dim_provider_history` | `provider_id` not_null (not unique — SCD2) | — | — |
| `fct_encounters` | `encounter_id` unique + not_null | `readmitted_status` ∈ {NO, >30, <30} | `patient_nbr → dim_patient` (**error**); `admission_type_id → dim_admission_type` (**error**) |
| `dim_patient` | `patient_nbr` unique + not_null | — | — |
| `fct_hospital_admissions` | `admission_id` unique + not_null | `type_of_admission` ∈ {Emergency, Trauma, Urgent} | `patient_id → dim_hospital_patient` (**error**); `severity_of_illness → dim_severity` (**error**) |
| `dim_hospital_patient` | `patient_id` unique + not_null | — | — |
| `dim_severity` | `severity_of_illness` unique + not_null | — | — |

**Fact** (from ADR-003 and `dbt/models/marts/schema.yml`): The `fct_claims.bene_id →
dim_beneficiary` relationship test is set to `severity: warn`, not `error`. This is
intentional: ~30 beneficiary rows were rejected by pandera at ingestion, leaving ~88
orphan claims in `fct_claims` with no matching `dim_beneficiary` row. These orphans
will appear on every `dbt test` run as a WARN, not a failure. The provider relationship
is a hard ERROR — if providers go missing, something is structurally wrong.

**Fact** (from `dbt/models/marts/schema.yml` description for `dim_hospital_patient`):
`dim_hospital_patient` is a **behavioural rollup** (admission counts, avg LOS, deposit
totals) — it carries **no stable demographics** because the synthetic source has no
consistent per-patient demographic columns. This is structurally different from
`dim_patient` (diabetes), which carries demographics from the patient's latest encounter.

### SCD2 temporal invariants

**Fact** (from `dbt/snapshots/snap_provider_fraud.sql` via `docs/incremental_scd2.md`
and `dbt/tests/`): Two singular tests enforce `dim_provider_history` integrity:
- `assert_provider_history_no_overlap` — no overlapping validity windows per provider.
- `assert_provider_history_one_current` — exactly one open row (`valid_to IS NULL`)
  per provider.

These are the only tests with temporal semantics. All other mart tests are point-in-time
(uniqueness, not_null, accepted_values, FK).

### Known quality gaps (don't discover these by accident)

**Fact** (from ADR-003, pandera run output, and `dbt/models/marts/schema.yml`):
1. ~30 beneficiaries are rejected at ingestion → written to `data/rejected/beneficiary_rejected.csv`.
2. ~88 claims in `fct_claims` reference those rejected beneficiaries → `bene_id` has no `dim_beneficiary` row. These pass dbt tests at `warn` severity.
3. `dim_provider.is_potential_fraud` is NULL for all providers from the Test split CSV.
   **Fact** (from `loaders.py` — `load_and_merge`): The Test split has no `PotentialFraud` column;
   the loader adds `NaN` before concatenation, which becomes SQL NULL. Analysts cannot
   distinguish "fraud label missing" from "provider not flagged as fraud" without filtering
   `is_potential_fraud IS NULL`.
4. `Bed Grade` (31 NULLs) and `City_Code_Patient` (121 NULLs) in the hospital source
   are legitimately nullable — the pandera schema marks them nullable accordingly.
5. `weight` (96.9% NULL), `medical_specialty` (49.1% NULL), `payer_code` (39.6% NULL)
   in the diabetes source — these are the `?`-recoded columns. High null rates are
   expected; they are not pipeline failures.

## Sources
- `src/clinical_data_etl/ingestion/schemas.py` — the pandera schemas: what each table's row must look like before loading
- `src/clinical_data_etl/ingestion/loaders.py` — pre-validation recodes, upsert logic, `ingested_at` audit stamp
- `dbt/models/marts/schema.yml` — mart-layer dbt tests: the downstream guarantees
- `dbt/models/intermediate/int_claims_unified.sql` — NULL-fill pattern for outpatient union columns
- [`docs/data-dictionary.md`](../docs/data-dictionary.md) — column-level raw→staging type and nullability reference
- [`docs/adr/003-reject-and-continue-validation.md`](../docs/adr/003-reject-and-continue-validation.md) — reject policy and orphan-claims decision

## Uncertainties & contradictions
- **Unresolved:** `validate_marts_task` in `orchestration/tasks.py` queries `raw_marts.*`, while the dbt profiles likely use a different schema name in practice. **Inference:** the schema name used in Prefect validation may diverge from the actual dbt target schema depending on the environment; the `.env` configuration determines the actual schema.
- **Unresolved:** No volume-threshold alert on rejected rows (noted in ADR-003 as future work). A spike in rejections (e.g., from a Kaggle re-download with a changed schema) would produce only a printed count, not a pipeline failure.
- **Inference:** `DiabetesEncounterSchema` validates column `A1Cresult` (camelCase from the source). The staging model renames it to `a1c_result`. The schema validates before the rename — **this is the correct order** but it means pandera schema column names and staging column names are intentionally different for this column.

## Related pages
- [Pipeline-Architecture](Pipeline-Architecture.md) — per-source quirks and overall pipeline shape; this page goes deeper on layer-by-layer guarantees

## Relevance to current work
Any new source added via `/add-source` must: (1) add a pandera schema to `schemas.py`,
(2) add a pre-validation clean function if the source has a sentinel or artifact,
(3) register a natural key in `NATURAL_KEYS`, and (4) add dbt tests (unique + not_null
on the grain, relationships on FKs, accepted_values on coded categoricals). The orphan-
claims warn pattern should be replicated only if there is a known, quantified reason for
orphans; otherwise FK relationships should be hard ERRORs.

_Last reviewed: 2026-07-26_
