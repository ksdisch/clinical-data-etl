{{
    config(
        materialized='incremental',
        unique_key='claim_id',
        incremental_strategy='delete+insert',
        on_schema_change='sync_all_columns'
    )
}}

with claims as (

    select * from {{ ref('int_claims_unified') }} src
    {% if is_incremental() %}
    -- Static 2009 data has no time delta, so the honest "new rows only" boundary
    -- is claim_id set-membership: only claims not yet materialised here. Use
    -- NOT EXISTS (not NOT IN) so Postgres plans a hash anti-join instead of a
    -- per-row subplan — the latter is pathologically slow over ~693k claims.
    where not exists (select 1 from {{ this }} t where t.claim_id = src.claim_id)
    {% endif %}

),

beneficiaries as (

    select * from {{ ref('stg_beneficiary') }}

)

select
    c.claim_id,
    c.bene_id,
    c.provider_id,
    c.claim_type,
    c.claim_start_date,
    c.claim_end_date,
    c.admission_date,
    c.discharge_date,
    c.claim_duration_days,
    c.reimbursement_amount,
    c.deductible_amount,
    c.attending_physician,
    c.operating_physician,
    c.other_physician,
    c.admit_diagnosis_code,
    c.diagnosis_group_code,
    c.diagnosis_code_1,
    c.diagnosis_code_2,
    c.diagnosis_code_3,
    c.diagnosis_code_4,
    c.diagnosis_code_5,
    c.diagnosis_code_6,
    c.diagnosis_code_7,
    c.diagnosis_code_8,
    c.diagnosis_code_9,
    c.diagnosis_code_10,
    c.procedure_code_1,
    c.procedure_code_2,
    c.procedure_code_3,
    c.procedure_code_4,
    c.procedure_code_5,
    c.procedure_code_6,

    -- Beneficiary demographics
    b.gender,
    b.race,
    b.date_of_birth,

    -- Age at time of claim
    extract(year from age(c.claim_start_date, b.date_of_birth))::int as age_at_claim,

    -- Chronic conditions
    b.has_alzheimers,
    b.has_heart_failure,
    b.has_kidney_disease,
    b.has_cancer,
    b.has_obstr_pulmonary,
    b.has_depression,
    b.has_diabetes,
    b.has_ischemic_heart,
    b.has_osteoporosis,
    b.has_rheumatoid_arthritis,
    b.has_stroke

from claims c
left join beneficiaries b on c.bene_id = b.bene_id
