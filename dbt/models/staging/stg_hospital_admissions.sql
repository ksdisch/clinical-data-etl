-- Cleaned hospital-admissions staging (TERTIARY source). One row per admission.
-- Renames the space-containing source columns to snake_case and casts types.
-- The surrogate admission_id and the '20-Nov'->'11-20' bracket recode are done
-- upstream at ingestion (clean_hospital_frame), so this layer is pure renaming.

with source as (

    select * from {{ source('raw', 'hospital_admissions') }}

)

select
    -- Keys
    "admission_id"                          as admission_id,
    -- case_id is a recycled source label (NOT unique); kept as a degenerate dim
    "case_id"                               as case_id,
    "patientid"                             as patient_id,

    -- Hospital attributes (degenerate dims — codes are randomized, no clean FD)
    "Hospital_code"::int                    as hospital_code,
    "Hospital_type_code"                    as hospital_type_code,
    "City_Code_Hospital"::int               as city_code_hospital,
    "Hospital_region_code"                  as hospital_region_code,
    "Ward_Type"                             as ward_type,
    "Ward_Facility_Code"                    as ward_facility_code,
    "Department"                            as department,
    "Bed Grade"::int                        as bed_grade,
    "Available Extra Rooms in Hospital"::int as available_extra_rooms,

    -- Patient / admission context
    "City_Code_Patient"::int                as city_code_patient,
    "Type of Admission"                     as type_of_admission,
    "Severity of Illness"                   as severity_of_illness,
    "Visitors with Patient"::int            as visitors_with_patient,
    "Age"                                   as age_bracket,

    -- Measures
    "Admission_Deposit"::numeric            as admission_deposit,

    -- Analytical target — length-of-stay bracket ('11-20' after the recode)
    "Stay"                                  as length_of_stay_bracket

from source
