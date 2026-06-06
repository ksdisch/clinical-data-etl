-- Patient dimension for the hospital star (grain: one row per patient_id).
-- A behavioural rollup, not a demographic dimension: the synthetic source has no
-- stable per-patient demographics (and ~98% of patients appear exactly once), so
-- this aggregates each patient's admission behaviour. The small repeat-admission
-- cohort (patients with total_admissions > 1) is the analytically interesting
-- slice. Mirrors dim_patient's aggregate role on the diabetes side.

select
    patient_id,
    count(*)                              as total_admissions,
    count(distinct hospital_code)         as distinct_hospitals,
    round(avg(length_of_stay_days), 2)    as avg_length_of_stay_days,
    sum(length_of_stay_days)              as total_length_of_stay_days,
    sum(admission_deposit)                as total_admission_deposit,
    round(avg(admission_deposit), 2)      as avg_admission_deposit
from {{ ref('int_admissions_enriched') }}
group by patient_id
