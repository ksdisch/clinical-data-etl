# Data Sources & Folder Layout

## Data Sources

### PRIMARY — Medicare Claims Fraud Detection
Source: Kaggle `rohitrox/healthcare-provider-fraud-detection-analysis`
Location: `data/raw/claims_fraud/`

| File | Description |
|------|-------------|
| `Train_Beneficiarydata-1542865627584.csv` | Beneficiary demographics: BeneID, DOB, DOD, Gender, Race, chronic condition flags, reimbursement amounts |
| `Test_Beneficiarydata-1542969243754.csv` | Beneficiary test split |
| `Train_Inpatientdata-1542865627584.csv` | Inpatient claims: BeneID, ClaimID, Provider, diagnosis/procedure codes, admission/discharge dates, reimbursement |
| `Test_Inpatientdata-1542969243754.csv` | Inpatient claims test split |
| `Train_Outpatientdata-1542865627584.csv` | Outpatient claims: same structure as inpatient, no admission dates |
| `Test_Outpatientdata-1542969243754.csv` | Outpatient claims test split |
| `Train-1542865627584.csv` | Provider fraud labels (Provider ID + PotentialFraud indicator) — train split |
| `Test-1542969243754.csv` | Provider fraud labels — test split (no PotentialFraud column; loader adds `NaN`) |

### SECONDARY — Diabetes Readmission (WIRED — second fact table)
Source: Kaggle `brandao/diabetes` (UCI Diabetes 130-US-hospitals, 1999–2008)
Location: `data/raw/diabetes_readmission/`
- `diabetic_data.csv` — **101,766 hospital encounters, 50 columns**, readmission outcome.

| Aspect | Detail |
|--------|--------|
| Grain | one row per `encounter_id` (verified unique) → `fct_encounters` |
| Patient key | `patient_nbr` (71,518 distinct) → `dim_patient` |
| Missing sentinel | the literal string `?` (recoded to NULL at ingestion before pandera validation) |
| Outcome | `readmitted` ∈ {`NO`, `>30`, `<30`}; analytical target `is_readmitted_30d` = (`<30`) |
| Notable columns | 23 medication dose-change columns, 3 ICD-9 diagnoses, A1C/glucose labs, admission/discharge id codes |
| Lookup seed | `admission_type_id` → label via `dbt/seeds/admission_type_mapping.csv` (`dim_admission_type`) |

No natural key joins the diabetes and claims data — they are modelled as two
**independent star schemas** sharing the same ingestion/validation/dbt patterns.

### TERTIARY — Synthetic Hospital (Phase 2)
Source: Kaggle `amulyas/synthetic-hospital-data`
Location: `data/raw/synthetic_hospital/`
- `HospitalSynthetic1.csv` — Lightweight dataset for testing and development

## Folder Layout

```
clinical-data-etl/
├── CLAUDE.md
├── Makefile
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── data/
│   └── raw/
│       ├── claims_fraud/           # Medicare claims fraud CSVs (primary)
│       ├── diabetes_readmission/   # Diabetes readmission CSV (secondary)
│       └── synthetic_hospital/     # Synthetic hospital CSV (tertiary)
├── src/
│   └── clinical_data_etl/
│       ├── ingestion/      # CSV loading, pandera schemas, DB writes
│       │   ├── loaders.py
│       │   └── schemas.py
│       ├── orchestration/  # Prefect flows and tasks
│       │   ├── flows.py
│       │   └── tasks.py
│       └── utils/          # DB connections, config, shared helpers
│           └── db.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── snapshots/
│   ├── seeds/
│   ├── macros/
│   └── tests/
└── tests/                  # pytest tests for Python code
    ├── conftest.py
    ├── test_ingestion/
    └── test_utils/
```
