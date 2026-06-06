{{
    config(
        materialized='incremental',
        unique_key='admission_id',
        incremental_strategy='delete+insert',
        on_schema_change='sync_all_columns'
    )
}}

-- Third fact table (grain: one hospital admission). Incremental like fct_claims
-- and fct_encounters so the production-shaping story holds across all three
-- sources. FK admission_id context: patient_id -> dim_hospital_patient,
-- severity_of_illness -> dim_severity. Hospital/ward/department codes are kept
-- as degenerate dimensions (the source codes are randomized, so there is no
-- clean entity to conform them into).

select
    admission_id,

    -- Degenerate dimensions
    case_id,
    patient_id,
    hospital_code,
    hospital_type_code,
    city_code_hospital,
    hospital_region_code,
    ward_type,
    ward_facility_code,
    department,
    bed_grade,
    city_code_patient,
    type_of_admission,
    severity_of_illness,
    age_bracket,

    -- Measures
    available_extra_rooms,
    visitors_with_patient,
    admission_deposit,
    length_of_stay_bracket,
    length_of_stay_days,

    -- Outcome
    is_long_stay

from {{ ref('int_admissions_enriched') }} src
{% if is_incremental() %}
-- NOT EXISTS (not NOT IN) so Postgres plans a hash anti-join, keeping re-runs fast.
where not exists (select 1 from {{ this }} t where t.admission_id = src.admission_id)
{% endif %}
