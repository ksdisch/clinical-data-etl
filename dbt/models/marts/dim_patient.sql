-- Patient dimension for the diabetes star (grain: one row per patient_nbr).
-- A patient can have many encounters, so demographics are taken from the
-- patient's most recent encounter and the readmission rollups aggregate all
-- of their encounters.

with latest_demographics as (

    select distinct on (patient_nbr)
        patient_nbr,
        race,
        gender,
        age_bracket
    from {{ ref('stg_diabetes_encounters') }}
    -- encounter_id is a stringified integer; cast so "latest" is numeric, not lexical
    order by patient_nbr, encounter_id::bigint desc

),

rollup as (

    select
        patient_nbr,
        count(*)                                          as total_encounters,
        sum(case when is_readmitted_30d then 1 else 0 end) as num_readmissions_30d,
        round(
            avg(case when is_readmitted_30d then 1.0 else 0.0 end), 4
        )                                                 as readmission_30d_rate
    from {{ ref('stg_diabetes_encounters') }}
    group by patient_nbr

)

select
    r.patient_nbr,
    d.race,
    d.gender,
    d.age_bracket as latest_age_bracket,
    r.total_encounters,
    r.num_readmissions_30d,
    r.readmission_30d_rate
from rollup r
join latest_demographics d using (patient_nbr)
