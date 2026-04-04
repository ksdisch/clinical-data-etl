-- Reimbursement amounts should never be negative.
-- This test passes when zero rows are returned (no violations).

select
    claim_id,
    reimbursement_amount
from {{ ref('fct_claims') }}
where reimbursement_amount < 0
