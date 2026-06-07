# ADR-004: Model three independent stars, no conformed cross-source key

**Status:** Accepted

## Context

The warehouse ingests three unrelated healthcare datasets: Medicare claims fraud (primary), UCI
diabetes readmission (secondary), and synthetic hospital length-of-stay (tertiary). There is a
temptation, when several datasets live in one warehouse, to force conformed dimensions or a shared
patient key across them. But these three sources share **no real-world key**: a Medicare `BeneID`, a
diabetes `patient_nbr`, and a synthetic `patientid` refer to disjoint populations from different
provenances and vintages. Any join across them would be a fabricated relationship.

## Decision

Model each source as its own **independent star schema**, sharing only the *patterns*
(ingest → pandera → `raw` → `stg_` → `int_` → `fct_`/`dim_`), never keys:

- **Claims:** `fct_claims` + `dim_beneficiary` + `dim_provider` (+ `dim_provider_history`).
- **Diabetes:** `fct_encounters` + `dim_patient` + `dim_admission_type`.
- **Hospital:** `fct_hospital_admissions` + `dim_hospital_patient` + `dim_severity`.

No `ref()` or foreign key crosses a star boundary. The three fact tables are never unioned or joined.

## Consequences

- **Easier:** each star is independently correct, testable, and re-runnable; adding a fourth source is
  a repeat of the same pattern with zero coupling to the existing three (proven twice — diabetes, then
  hospital).
- **Easier (portfolio):** demonstrates that the ingest/model pattern *generalises*, which is a stronger
  signal than a single bespoke pipeline.
- **Harder / accepted:** there is no single "patient 360" view across sources — correct, because no such
  entity exists in this data. If a future real source genuinely conformed (e.g. shared a provider
  registry), a conformed dimension would warrant its own ADR.
