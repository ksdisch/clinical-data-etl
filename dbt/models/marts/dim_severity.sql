-- Conformed lookup dimension for the hospital star, built from the
-- severity_mapping seed. Turns the 'Severity of Illness' category on
-- fct_hospital_admissions into an ordinal rank (Minor=1, Moderate=2, Extreme=3)
-- plus a human-readable description. Mirrors dim_admission_type's seed-backed
-- role on the diabetes side.

select
    severity_of_illness,
    severity_rank,
    severity_description
from {{ ref('severity_mapping') }}
