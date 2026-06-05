with source as (

    select * from {{ source('raw', 'diabetes_encounters') }}

)

select
    -- Keys
    "encounter_id"                          as encounter_id,
    "patient_nbr"                           as patient_nbr,

    -- Demographics
    "race"                                  as race,
    "gender"                                as gender,
    "age"                                   as age_bracket,
    "weight"                                as weight,

    -- Encounter context (degenerate dimensions; *_id values map via seeds/docs)
    "admission_type_id"::int                as admission_type_id,
    "discharge_disposition_id"::int         as discharge_disposition_id,
    "admission_source_id"::int              as admission_source_id,
    "medical_specialty"                     as medical_specialty,
    "payer_code"                            as payer_code,

    -- Utilisation measures
    "time_in_hospital"::int                 as time_in_hospital,
    "num_lab_procedures"::int               as num_lab_procedures,
    "num_procedures"::int                   as num_procedures,
    "num_medications"::int                  as num_medications,
    "number_outpatient"::int                as number_outpatient,
    "number_emergency"::int                 as number_emergency,
    "number_inpatient"::int                 as number_inpatient,
    "number_diagnoses"::int                 as number_diagnoses,

    -- Diagnoses (ICD-9 codes) and labs
    "diag_1"                                as diag_1,
    "diag_2"                                as diag_2,
    "diag_3"                                as diag_3,
    "max_glu_serum"                         as max_glu_serum,
    "A1Cresult"                             as a1c_result,

    -- Medications (dose change: No / Steady / Up / Down)
    "metformin"                             as metformin,
    "repaglinide"                           as repaglinide,
    "nateglinide"                           as nateglinide,
    "chlorpropamide"                        as chlorpropamide,
    "glimepiride"                           as glimepiride,
    "acetohexamide"                         as acetohexamide,
    "glipizide"                             as glipizide,
    "glyburide"                             as glyburide,
    "tolbutamide"                           as tolbutamide,
    "pioglitazone"                          as pioglitazone,
    "rosiglitazone"                         as rosiglitazone,
    "acarbose"                              as acarbose,
    "miglitol"                              as miglitol,
    "troglitazone"                          as troglitazone,
    "tolazamide"                            as tolazamide,
    "examide"                               as examide,
    "citoglipton"                           as citoglipton,
    "insulin"                               as insulin,
    "glyburide-metformin"                   as glyburide_metformin,
    "glipizide-metformin"                   as glipizide_metformin,
    "glimepiride-pioglitazone"              as glimepiride_pioglitazone,
    "metformin-rosiglitazone"               as metformin_rosiglitazone,
    "metformin-pioglitazone"                as metformin_pioglitazone,

    -- Boolean derivations (1:1 row transforms)
    ("change" = 'Ch')                       as had_med_change,
    ("diabetesMed" = 'Yes')                 as on_diabetes_med,

    -- Outcome: 3-class status plus the analytical 30-day readmission flag
    "readmitted"                            as readmitted_status,
    ("readmitted" = '<30')                  as is_readmitted_30d

from source
