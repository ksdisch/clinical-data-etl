with source as (

    select * from {{ source('raw', 'outpatient_claims') }}

)

select
    "BeneID"                              as bene_id,
    "ClaimID"                             as claim_id,
    "Provider"                            as provider_id,
    'outpatient'                          as claim_type,
    "ClaimStartDt"::date                  as claim_start_date,
    "ClaimEndDt"::date                    as claim_end_date,
    "InscClaimAmtReimbursed"::numeric(12,2) as reimbursement_amount,
    "DeductibleAmtPaid"::numeric(12,2)    as deductible_amount,
    "AttendingPhysician"                  as attending_physician,
    "OperatingPhysician"                  as operating_physician,
    "OtherPhysician"                      as other_physician,
    "ClmAdmitDiagnosisCode"              as admit_diagnosis_code,
    "ClmDiagnosisCode_1"                  as diagnosis_code_1,
    "ClmDiagnosisCode_2"                  as diagnosis_code_2,
    "ClmDiagnosisCode_3"                  as diagnosis_code_3,
    "ClmDiagnosisCode_4"                  as diagnosis_code_4,
    "ClmDiagnosisCode_5"                  as diagnosis_code_5,
    "ClmDiagnosisCode_6"                  as diagnosis_code_6,
    "ClmDiagnosisCode_7"                  as diagnosis_code_7,
    "ClmDiagnosisCode_8"                  as diagnosis_code_8,
    "ClmDiagnosisCode_9"                  as diagnosis_code_9,
    "ClmDiagnosisCode_10"                 as diagnosis_code_10,
    "ClmProcedureCode_1"                  as procedure_code_1,
    "ClmProcedureCode_2"                  as procedure_code_2,
    "ClmProcedureCode_3"                  as procedure_code_3,
    "ClmProcedureCode_4"                  as procedure_code_4,
    "ClmProcedureCode_5"                  as procedure_code_5,
    "ClmProcedureCode_6"                  as procedure_code_6

from source
