-- The 30-day readmission boolean must be true exactly when the 3-class status
-- is '<30'. Any row where the two disagree is a derivation bug. Returns the
-- offending rows (0 = pass).

select
    encounter_id,
    readmitted_status,
    is_readmitted_30d
from {{ ref('fct_encounters') }}
where is_readmitted_30d <> (readmitted_status = '<30')
