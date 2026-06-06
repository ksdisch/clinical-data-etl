{{
    config(
        materialized='incremental',
        unique_key='encounter_id',
        incremental_strategy='delete+insert',
        on_schema_change='sync_all_columns'
    )
}}

-- Second fact table (grain: one hospital encounter). Incremental like
-- fct_claims so the production-shaping story holds across both sources.
-- FK encounter_id -> dim_patient (patient_nbr) and admission_type_id ->
-- dim_admission_type.

select
    encounter_id,
    patient_nbr,

    -- Degenerate / FK context
    admission_type_id,
    discharge_disposition_id,
    admission_source_id,
    medical_specialty,
    age_bracket,

    -- Utilisation measures
    time_in_hospital,
    num_lab_procedures,
    num_procedures,
    num_medications,
    number_outpatient,
    number_emergency,
    number_inpatient,
    number_diagnoses,
    num_prior_visits,
    num_diabetes_meds,

    -- Diagnoses and labs
    diag_1,
    diag_2,
    diag_3,
    max_glu_serum,
    a1c_result,

    -- Medication signals
    insulin,
    metformin,
    had_med_change,
    on_diabetes_med,

    -- Outcome
    readmitted_status,
    is_readmitted_30d

from {{ ref('int_encounters_enriched') }} src
{% if is_incremental() %}
-- NOT EXISTS (not NOT IN) so Postgres plans a hash anti-join, keeping re-runs fast.
where not exists (select 1 from {{ this }} t where t.encounter_id = src.encounter_id)
{% endif %}
