-- Age at claim should be between 0 and 120.
-- NULL age is acceptable (beneficiary not matched).
-- This test passes when zero rows are returned (no violations).

select
    claim_id,
    age_at_claim
from {{ ref('int_claims_enriched') }}
where age_at_claim is not null
  and (age_at_claim < 0 or age_at_claim > 120)
