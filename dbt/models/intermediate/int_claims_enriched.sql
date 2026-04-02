with claims as (

    select * from {{ ref('int_claims_unified') }}

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
