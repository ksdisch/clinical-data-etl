-- Hospital admissions with derived analytical features. Mirrors the role of
-- int_encounters_enriched on the diabetes side: a view that adds computed fields
-- on top of the cleaned staging grain (one row per admission). No dimension join
-- here — patient rollups live in dim_hospital_patient (an aggregate) to avoid a
-- cycle.

with admissions as (

    select * from {{ ref('stg_hospital_admissions') }}

),

with_los_days as (

    select
        *,
        -- Length of stay is bucketed in 10-day brackets in the source; map each
        -- to its midpoint so it can be averaged/aggregated as a numeric measure.
        -- 'More than 100 Days' -> 105 (open-ended top bucket).
        case length_of_stay_bracket
            when '0-10'  then 5
            when '11-20' then 15
            when '21-30' then 25
            when '31-40' then 35
            when '41-50' then 45
            when '51-60' then 55
            when '61-70' then 65
            when '71-80' then 75
            when '81-90' then 85
            when '91-100' then 95
            when 'More than 100 Days' then 105
        end as length_of_stay_days
    from admissions

)

select
    admission_id,
    case_id,
    patient_id,

    -- Hospital / ward context carried onto the fact grain
    hospital_code,
    hospital_type_code,
    city_code_hospital,
    hospital_region_code,
    ward_type,
    ward_facility_code,
    department,
    bed_grade,
    available_extra_rooms,

    -- Patient / admission context
    city_code_patient,
    type_of_admission,
    severity_of_illness,
    visitors_with_patient,
    age_bracket,

    -- Measures
    admission_deposit,
    length_of_stay_bracket,
    length_of_stay_days,

    -- Outcome: binary analytical target (mirrors diabetes' is_readmitted_30d)
    (length_of_stay_days > 30) as is_long_stay

from with_los_days
