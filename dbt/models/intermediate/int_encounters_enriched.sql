-- Diabetes encounters with derived analytical features. Mirrors the role of
-- int_claims_enriched on the claims side: a view that adds computed fields on
-- top of the cleaned staging grain (one row per encounter). No dimension join
-- here — patient rollups live in dim_patient (an aggregate) to avoid a cycle.

with encounters as (

    select * from {{ ref('stg_diabetes_encounters') }}

)

select
    encounter_id,
    patient_nbr,

    -- Demographics / context carried onto the fact grain
    race,
    gender,
    age_bracket,
    admission_type_id,
    discharge_disposition_id,
    admission_source_id,
    medical_specialty,

    -- Utilisation measures
    time_in_hospital,
    num_lab_procedures,
    num_procedures,
    num_medications,
    number_outpatient,
    number_emergency,
    number_inpatient,
    number_diagnoses,

    -- Derived: prior-care utilisation across the year before this encounter
    (number_outpatient + number_emergency + number_inpatient) as num_prior_visits,

    -- Derived: how many of the 23 tracked drugs were actively prescribed
    (
        (metformin <> 'No')::int
        + (repaglinide <> 'No')::int
        + (nateglinide <> 'No')::int
        + (chlorpropamide <> 'No')::int
        + (glimepiride <> 'No')::int
        + (acetohexamide <> 'No')::int
        + (glipizide <> 'No')::int
        + (glyburide <> 'No')::int
        + (tolbutamide <> 'No')::int
        + (pioglitazone <> 'No')::int
        + (rosiglitazone <> 'No')::int
        + (acarbose <> 'No')::int
        + (miglitol <> 'No')::int
        + (troglitazone <> 'No')::int
        + (tolazamide <> 'No')::int
        + (examide <> 'No')::int
        + (citoglipton <> 'No')::int
        + (insulin <> 'No')::int
        + (glyburide_metformin <> 'No')::int
        + (glipizide_metformin <> 'No')::int
        + (glimepiride_pioglitazone <> 'No')::int
        + (metformin_rosiglitazone <> 'No')::int
        + (metformin_pioglitazone <> 'No')::int
    ) as num_diabetes_meds,

    -- Diagnoses and labs
    diag_1,
    diag_2,
    diag_3,
    max_glu_serum,
    a1c_result,

    -- Key individual medication signals kept on the grain
    insulin,
    metformin,
    had_med_change,
    on_diabetes_med,

    -- Outcome
    readmitted_status,
    is_readmitted_30d

from encounters
