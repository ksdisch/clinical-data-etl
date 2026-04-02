with inpatient as (

    select
        bene_id,
        claim_id,
        provider_id,
        claim_type,
        claim_start_date,
        claim_end_date,
        admission_date,
        discharge_date,
        claim_duration_days,
        reimbursement_amount,
        deductible_amount,
        attending_physician,
        operating_physician,
        other_physician,
        admit_diagnosis_code,
        diagnosis_group_code,
        diagnosis_code_1,
        diagnosis_code_2,
        diagnosis_code_3,
        diagnosis_code_4,
        diagnosis_code_5,
        diagnosis_code_6,
        diagnosis_code_7,
        diagnosis_code_8,
        diagnosis_code_9,
        diagnosis_code_10,
        procedure_code_1,
        procedure_code_2,
        procedure_code_3,
        procedure_code_4,
        procedure_code_5,
        procedure_code_6

    from {{ ref('stg_inpatient_claims') }}

),

outpatient as (

    select
        bene_id,
        claim_id,
        provider_id,
        claim_type,
        claim_start_date,
        claim_end_date,
        null::date              as admission_date,
        null::date              as discharge_date,
        null::integer           as claim_duration_days,
        reimbursement_amount,
        deductible_amount,
        attending_physician,
        operating_physician,
        other_physician,
        admit_diagnosis_code,
        null::text              as diagnosis_group_code,
        diagnosis_code_1,
        diagnosis_code_2,
        diagnosis_code_3,
        diagnosis_code_4,
        diagnosis_code_5,
        diagnosis_code_6,
        diagnosis_code_7,
        diagnosis_code_8,
        diagnosis_code_9,
        diagnosis_code_10,
        procedure_code_1,
        procedure_code_2,
        procedure_code_3,
        procedure_code_4,
        procedure_code_5,
        procedure_code_6

    from {{ ref('stg_outpatient_claims') }}

)

select * from inpatient
union all
select * from outpatient
