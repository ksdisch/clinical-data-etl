with providers as (

    select * from {{ ref('stg_providers') }}

),

claim_metrics as (

    select
        provider_id,
        count(*)                                    as total_claims,
        sum(reimbursement_amount)                   as total_reimbursement,
        count(distinct bene_id)                     as unique_beneficiaries,
        avg(reimbursement_amount)::numeric(12,2)    as avg_reimbursement_per_claim

    from {{ ref('int_claims_unified') }}
    group by provider_id

)

select
    p.provider_id,
    p.is_potential_fraud,
    coalesce(m.total_claims, 0)               as total_claims,
    coalesce(m.total_reimbursement, 0)        as total_reimbursement,
    coalesce(m.unique_beneficiaries, 0)       as unique_beneficiaries,
    coalesce(m.avg_reimbursement_per_claim, 0) as avg_reimbursement_per_claim

from providers p
left join claim_metrics m on p.provider_id = m.provider_id
