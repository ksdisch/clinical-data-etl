-- Claims where start date is after end date indicate data quality issues.
-- This test passes when zero rows are returned (no violations).

select
    claim_id,
    claim_start_date,
    claim_end_date
from {{ ref('int_claims_enriched') }}
where claim_start_date > claim_end_date
