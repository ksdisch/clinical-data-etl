-- Length of stay (bracket midpoint, in days) should never be negative or NULL.
-- A NULL means the source Stay bracket fell outside the known set and the
-- midpoint CASE produced no match. This test passes when zero rows are returned.

select
    admission_id,
    length_of_stay_bracket,
    length_of_stay_days
from {{ ref('fct_hospital_admissions') }}
where length_of_stay_days is null
   or length_of_stay_days < 0
