with source as (

    select * from {{ source('raw', 'beneficiary') }}

)

select
    "BeneID"                          as bene_id,
    "DOB"::date                       as date_of_birth,
    "DOD"::date                       as date_of_death,
    case "Gender"
        when 1 then 'Male'
        when 2 then 'Female'
    end                               as gender,
    case "Race"
        when 1 then 'White'
        when 2 then 'Black'
        when 3 then 'Other'
        when 5 then 'Hispanic'
        else 'Unknown'
    end                               as race,
    "RenalDiseaseIndicator"           as renal_disease_indicator,
    "State"                           as state_code,
    "County"                          as county_code,
    "NoOfMonths_PartACov"             as months_part_a_coverage,
    "NoOfMonths_PartBCov"             as months_part_b_coverage,

    -- Chronic conditions: 1 = yes, 2 = no → boolean
    ("ChronicCond_Alzheimer" = 1)           as has_alzheimers,
    ("ChronicCond_Heartfailure" = 1)        as has_heart_failure,
    ("ChronicCond_KidneyDisease" = 1)       as has_kidney_disease,
    ("ChronicCond_Cancer" = 1)              as has_cancer,
    ("ChronicCond_ObstrPulmonary" = 1)      as has_obstr_pulmonary,
    ("ChronicCond_Depression" = 1)          as has_depression,
    ("ChronicCond_Diabetes" = 1)            as has_diabetes,
    ("ChronicCond_IschemicHeart" = 1)       as has_ischemic_heart,
    ("ChronicCond_Osteoporasis" = 1)        as has_osteoporosis,
    ("ChronicCond_rheumatoidarthritis" = 1) as has_rheumatoid_arthritis,
    ("ChronicCond_stroke" = 1)              as has_stroke,

    "IPAnnualReimbursementAmt"::numeric(12,2)  as ip_annual_reimbursement,
    "IPAnnualDeductibleAmt"::numeric(12,2)     as ip_annual_deductible,
    "OPAnnualReimbursementAmt"::numeric(12,2)  as op_annual_reimbursement,
    "OPAnnualDeductibleAmt"::numeric(12,2)     as op_annual_deductible

from source
