-- The is_long_stay boolean must be true exactly when length_of_stay_days > 30.
-- Any row where the two disagree is a derivation bug. Returns the offending rows
-- (0 = pass). Mirrors assert_readmitted_flag_consistent on the diabetes side.

select
    admission_id,
    length_of_stay_days,
    is_long_stay
from {{ ref('fct_hospital_admissions') }}
where is_long_stay <> (length_of_stay_days > 30)
