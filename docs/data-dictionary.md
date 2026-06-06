# Data Dictionary

A column-level reference for all three independent star schemas. For each source it lists the **raw
source columns** (canonical name, type, nullability, and any recode / sentinel handling applied at
ingestion) and the **staging rename** the dbt `stg_*` model applies, then the **mart-facing** columns.

- Source of truth for raw types/nullability: `src/clinical_data_etl/ingestion/schemas.py` (pandera).
- Source of truth for renames: the `dbt/models/staging/stg_*.sql` models.
- Source of truth for mart semantics: `dbt/models/marts/schema.yml` (this dictionary summarises it).
- For the decisions behind the recodes and surrogate keys, see [`docs/adr/`](adr/).

Conventions: types are the **post-cast** types (what staging produces). "Recode" means a transform
the loader applies *before* pandera validation; "derived" means a column computed in dbt with no direct
source column.

---

## Star 1 — Medicare Claims Fraud (PRIMARY)

Kaggle `rohitrox/healthcare-provider-fraud-detection-analysis`. Train/Test CSV splits are merged at
ingest (ADR-001). Grain notes per table below.

### raw.beneficiary → `stg_beneficiary` (one row per beneficiary)

| Source column | Staging column | Type | Null | Notes |
|---|---|---|---|---|
| `BeneID` | `bene_id` | text | no | Beneficiary identifier (unique). |
| `DOB` | `date_of_birth` | date | no | Date of birth. |
| `DOD` | `date_of_death` | date | yes | Date of death; NULL if the beneficiary is alive. |
| `Gender` | `gender` | text | no | **Recoded** 1 → `Male`, 2 → `Female`. |
| `Race` | `race` | text | no | **Recoded** 1 `White`, 2 `Black`, 3 `Other`, 5 `Hispanic`, else `Unknown`. |
| `RenalDiseaseIndicator` | `renal_disease_indicator` | text | no | `Y` = end-stage renal disease, `0` otherwise. |
| `State` | `state_code` | int | no | CMS state code. |
| `County` | `county_code` | int | no | CMS county code. |
| `NoOfMonths_PartACov` | `months_part_a_coverage` | int | no | Months of Medicare Part A coverage (0–12). |
| `NoOfMonths_PartBCov` | `months_part_b_coverage` | int | no | Months of Medicare Part B coverage (0–12). |
| `ChronicCond_Alzheimer` | `has_alzheimers` | bool | no | **Recoded** 1 = yes → `true`, 2 = no → `false`. |
| `ChronicCond_Heartfailure` | `has_heart_failure` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_KidneyDisease` | `has_kidney_disease` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_Cancer` | `has_cancer` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_ObstrPulmonary` | `has_obstr_pulmonary` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_Depression` | `has_depression` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_Diabetes` | `has_diabetes` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_IschemicHeart` | `has_ischemic_heart` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_Osteoporasis` | `has_osteoporosis` | bool | no | Same 1/2 → bool recode (source spelling `Osteoporasis`). |
| `ChronicCond_rheumatoidarthritis` | `has_rheumatoid_arthritis` | bool | no | Same 1/2 → bool recode. |
| `ChronicCond_stroke` | `has_stroke` | bool | no | Same 1/2 → bool recode. |
| `IPAnnualReimbursementAmt` | `ip_annual_reimbursement` | numeric(12,2) | no | Annual inpatient reimbursement total (≥ 0). |
| `IPAnnualDeductibleAmt` | `ip_annual_deductible` | numeric(12,2) | no | Annual inpatient deductible total (≥ 0). |
| `OPAnnualReimbursementAmt` | `op_annual_reimbursement` | numeric(12,2) | no | Annual outpatient reimbursement total (≥ 0). |
| `OPAnnualDeductibleAmt` | `op_annual_deductible` | numeric(12,2) | no | Annual outpatient deductible total (≥ 0). |

### raw.inpatient_claims → `stg_inpatient_claims` (one row per claim)

| Source column | Staging column | Type | Null | Notes |
|---|---|---|---|---|
| `BeneID` | `bene_id` | text | no | FK to beneficiary. |
| `ClaimID` | `claim_id` | text | no | Claim identifier (unique). |
| `Provider` | `provider_id` | text | no | FK to provider. |
| *(constant)* | `claim_type` | text | no | Literal `'inpatient'`. |
| `ClaimStartDt` | `claim_start_date` | date | no | First date of the claim period. |
| `ClaimEndDt` | `claim_end_date` | date | no | Last date of the claim period. |
| `AdmissionDt` | `admission_date` | date | no | Hospital admission date (inpatient only). |
| `DischargeDt` | `discharge_date` | date | no | Hospital discharge date (inpatient only). |
| *(derived)* | `claim_duration_days` | int | no | `discharge_date − admission_date` in days. |
| `InscClaimAmtReimbursed` | `reimbursement_amount` | numeric(12,2) | no | Medicare reimbursement for this claim (≥ 0). |
| `DeductibleAmtPaid` | `deductible_amount` | numeric(12,2) | yes | Deductible applied to this claim. |
| `AttendingPhysician` | `attending_physician` | text | yes | Attending physician id. |
| `OperatingPhysician` | `operating_physician` | text | yes | Operating physician id. |
| `OtherPhysician` | `other_physician` | text | yes | Other physician id. |
| `ClmAdmitDiagnosisCode` | `admit_diagnosis_code` | text | yes | Admitting diagnosis (ICD-9). |
| `DiagnosisGroupCode` | `diagnosis_group_code` | text | yes | Diagnosis-related group (DRG) code. |
| `ClmDiagnosisCode_1`…`_10` | `diagnosis_code_1`…`_10` | text | yes | Up to 10 ICD-9 diagnosis codes. |
| `ClmProcedureCode_1`…`_6` | `procedure_code_1`…`_6` | text | yes | Up to 6 procedure codes. |

### raw.outpatient_claims → `stg_outpatient_claims` (one row per claim)

Same structure as inpatient **minus** `admission_date`, `discharge_date`, `claim_duration_days`, and
`diagnosis_group_code`; `claim_type` is the literal `'outpatient'`. When unioned into
`int_claims_unified`, those four columns are filled with `NULL` for outpatient rows (ADR — see
`int_claims_unified` description).

### raw.providers → `stg_providers` (one row per provider)

| Source column | Staging column | Type | Null | Notes |
|---|---|---|---|---|
| `Provider` | `provider_id` | text | no | Provider identifier (unique). |
| `PotentialFraud` | `is_potential_fraud` | bool | yes | **Recoded** `Yes` → `true`, `No` → `false`, else `NULL`. The **Test split CSV has no `PotentialFraud` column**; the loader adds `NaN`, which becomes `NULL` here (ADR-001). |

### Marts (claims star)

| Model | Grain | Key columns | Notes |
|---|---|---|---|
| `fct_claims` | one claim | `claim_id` (unique), `bene_id` → `dim_beneficiary`, `provider_id` → `dim_provider` | Carries `claim_type`, claim/admission/discharge dates, `claim_duration_days` (NULL for outpatient), `reimbursement_amount`, `deductible_amount`, `age_at_claim`. The `bene_id` relationship test is `severity: warn` — ~88 orphan claims from 30 pandera-rejected beneficiaries (ADR-003). |
| `dim_beneficiary` | one beneficiary | `bene_id` (unique) | Demographics + 11 `has_*` chronic flags + `chronic_condition_count` (0–11) + `total_ip_reimbursement` / `total_op_reimbursement`. |
| `dim_provider` | one provider | `provider_id` (unique) | Current `is_potential_fraud` (NULL for test-split providers) + aggregates: `total_claims`, `total_reimbursement`, `unique_beneficiaries`, `avg_reimbursement_per_claim`. Fraud label lives here, not on the fact (ADR-002). |
| `dim_provider_history` | one (provider, validity window) | `provider_id` (not unique), `valid_from`, `valid_to`, `is_current` | SCD2 history of `is_potential_fraud` from `snap_provider_fraud` (ADR-007). |

Full mart column descriptions live in `dbt/models/marts/schema.yml`.

---

## Star 2 — Diabetes Readmission (SECONDARY)

Kaggle `brandao/diabetes` (UCI 130-US-hospitals, 1999–2008). Single CSV, 101,766 encounters. The `?`
missing sentinel is recoded to NULL before validation.

### raw.diabetes_encounters → `stg_diabetes_encounters` (one row per encounter)

| Source column | Staging column | Type | Null | Notes |
|---|---|---|---|---|
| `encounter_id` | `encounter_id` | text | no | Encounter identifier (unique) — the grain. |
| `patient_nbr` | `patient_nbr` | text | no | Patient identifier (FK to `dim_patient`; 71,518 distinct). |
| `race` | `race` | text | yes | `?` → NULL. |
| `gender` | `gender` | text | no | One of `Female` / `Male` / `Unknown/Invalid`. |
| `age` | `age_bracket` | text | no | 10-year bracket `[0-10)` … `[90-100)`. |
| `weight` | `weight` | text | yes | Largely missing in source; `?` → NULL. |
| `admission_type_id` | `admission_type_id` | int | no | Code 1–8; labelled via `dim_admission_type` seed (ADR-010). |
| `discharge_disposition_id` | `discharge_disposition_id` | int | no | Discharge disposition code (≥ 1, degenerate dim). |
| `admission_source_id` | `admission_source_id` | int | no | Admission source code (≥ 1, degenerate dim). |
| `medical_specialty` | `medical_specialty` | text | yes | Admitting physician specialty; `?` → NULL. |
| `payer_code` | `payer_code` | text | yes | Payer code; `?` → NULL. |
| `time_in_hospital` | `time_in_hospital` | int | no | Length of stay in days (1–14). |
| `num_lab_procedures` | `num_lab_procedures` | int | no | Lab procedures during the encounter (≥ 0). |
| `num_procedures` | `num_procedures` | int | no | Non-lab procedures (≥ 0). |
| `num_medications` | `num_medications` | int | no | Distinct medications administered (≥ 0). |
| `number_outpatient` | `number_outpatient` | int | no | Prior-year outpatient visits (≥ 0). |
| `number_emergency` | `number_emergency` | int | no | Prior-year emergency visits (≥ 0). |
| `number_inpatient` | `number_inpatient` | int | no | Prior-year inpatient visits (≥ 0). |
| `number_diagnoses` | `number_diagnoses` | int | no | Diagnoses entered for the encounter (≥ 0). |
| `diag_1` / `diag_2` / `diag_3` | `diag_1` / `diag_2` / `diag_3` | text | yes | Primary / secondary / additional ICD-9 diagnosis. |
| `max_glu_serum` | `max_glu_serum` | text | yes | Glucose serum test: `Norm` / `>200` / `>300` (NULL if not taken). |
| `A1Cresult` | `a1c_result` | text | yes | A1C test: `Norm` / `>7` / `>8` (NULL if not taken). |
| 23 medication columns | same names (`-` → `_`) | text | no | Each dose-change signal ∈ `No` / `Steady` / `Up` / `Down`. e.g. `glyburide-metformin` → `glyburide_metformin`. |
| `change` | `had_med_change` | bool | no | **Derived** `('Ch')` → `true`, `('No')` → `false`. |
| `diabetesMed` | `on_diabetes_med` | bool | no | **Derived** `('Yes')` → `true`, `('No')` → `false`. |
| `readmitted` | `readmitted_status` | text | no | 3-class outcome `NO` / `>30` / `<30`. |
| *(derived)* | `is_readmitted_30d` | bool | no | `readmitted = '<30'` — the analytical target (~11% overall). |

### Marts (diabetes star)

| Model | Grain | Key columns | Notes |
|---|---|---|---|
| `fct_encounters` | one encounter | `encounter_id` (unique), `patient_nbr` → `dim_patient`, `admission_type_id` → `dim_admission_type` | Incremental. Carries `time_in_hospital`, `num_prior_visits`, `num_diabetes_meds` (0–23), `readmitted_status`, `is_readmitted_30d`. |
| `dim_patient` | one patient | `patient_nbr` (unique) | Demographics from the latest encounter + `total_encounters`, `num_readmissions_30d`, `readmission_30d_rate`. |
| `dim_admission_type` | one admission-type code | `admission_type_id` (unique, 1–8) | Seed-backed lookup → `admission_type_label`. |

---

## Star 3 — Synthetic Hospital Admissions (TERTIARY)

Kaggle `amulyas/synthetic-hospital-data` (AV Healthcare Analytics II length-of-stay). Single CSV, 5,000
admissions. Two ingest-time recodes (ADR-008): the `20-Nov` → `11-20` Excel-corruption fix on
`Age`/`Stay`, and the minted surrogate `admission_id = md5(case_id-patientid)`.

### raw.hospital_admissions → `stg_hospital_admissions` (one row per admission)

| Source column | Staging column | Type | Null | Notes |
|---|---|---|---|---|
| `admission_id` | `admission_id` | text | no | **Minted surrogate** `md5(case_id-patientid)` (unique) — the grain (ADR-008). |
| `case_id` | `case_id` | text | no | Recycled source label — **NOT unique**; kept as a degenerate dim. |
| `patientid` | `patient_id` | text | no | Patient identifier (FK to `dim_hospital_patient`; 4,876 distinct). |
| `Hospital_code` | `hospital_code` | int | no | Hospital code (randomized — degenerate dim). |
| `Hospital_type_code` | `hospital_type_code` | text | no | One of `a`…`g`. |
| `City_Code_Hospital` | `city_code_hospital` | int | no | Hospital city code. |
| `Hospital_region_code` | `hospital_region_code` | text | no | One of `X` / `Y` / `Z`. |
| `Ward_Type` | `ward_type` | text | no | One of `P` / `Q` / `R` / `S` / `T`. |
| `Ward_Facility_Code` | `ward_facility_code` | text | no | One of `A`…`F`. |
| `Department` | `department` | text | no | `TB & Chest disease` / `anesthesia` / `gynecology` / `radiotherapy` / `surgery`. |
| `Bed Grade` | `bed_grade` | int | yes | Ordinal bed quality 1–4 (31 source NULLs). |
| `Available Extra Rooms in Hospital` | `available_extra_rooms` | int | no | Spare rooms at admission (≥ 0). |
| `City_Code_Patient` | `city_code_patient` | int | yes | Patient city code (≥ 1; nullable). |
| `Type of Admission` | `type_of_admission` | text | no | `Emergency` / `Trauma` / `Urgent`. |
| `Severity of Illness` | `severity_of_illness` | text | no | `Minor` / `Moderate` / `Extreme` (FK to `dim_severity`). |
| `Visitors with Patient` | `visitors_with_patient` | int | no | Visitor count (≥ 0). |
| `Age` | `age_bracket` | text | no | 10-year bracket `0-10` … `91-100` (after the `20-Nov` → `11-20` recode). |
| `Admission_Deposit` | `admission_deposit` | numeric | no | Deposit collected at admission (≥ 0). |
| `Stay` | `length_of_stay_bracket` | text | no | LOS bracket incl. `More than 100 Days` — analytical target (after recode). |

### Marts (hospital star)

| Model | Grain | Key columns | Notes |
|---|---|---|---|
| `fct_hospital_admissions` | one admission | `admission_id` (unique surrogate), `patient_id` → `dim_hospital_patient`, `severity_of_illness` → `dim_severity` | Incremental. Carries `type_of_admission`, `length_of_stay_bracket`, `length_of_stay_days` (bracket midpoint 5–105), `is_long_stay` (> 30 days; ~48%), `admission_deposit`. Hospital/ward/department codes are degenerate dims. |
| `dim_hospital_patient` | one patient | `patient_id` (unique) | Behavioural rollup: `total_admissions`, `distinct_hospitals`, `avg/total_length_of_stay_days`, `total/avg_admission_deposit` (no stable per-patient demographics in the synthetic source). |
| `dim_severity` | one severity level | `severity_of_illness` (unique) | Seed-backed ordinal lookup → `severity_rank` (Minor 1, Moderate 2, Extreme 3) + `severity_description`. |

---

## Notes on derived analytical features

- **`length_of_stay_days`** (`int_admissions_enriched`): each `Stay` bracket mapped to its midpoint
  (`0-10` → 5, `11-20` → 15, …, `91-100` → 95, `More than 100 Days` → 105) so LOS can be averaged.
- **`num_prior_visits`** (`int_encounters_enriched`): `number_outpatient + number_emergency + number_inpatient`.
- **`num_diabetes_meds`** (`int_encounters_enriched`): count of the 23 tracked drugs whose value ≠ `No` (0–23).
- **`age_at_claim`** (`int_claims_enriched`): whole years between `date_of_birth` and `claim_start_date`.
- **`chronic_condition_count`** (`dim_beneficiary`): count of the 11 `has_*` flags that are `true` (0–11).
