-- SCD2 temporal-validity invariant: no two versions of the same provider may
-- have overlapping [valid_from, valid_to) windows. Returns offending rows
-- (test passes on zero rows).
with history as (

    select
        provider_id,
        valid_from,
        coalesce(valid_to, timestamp '9999-12-31') as valid_to
    from {{ ref('dim_provider_history') }}

)

select
    a.provider_id,
    a.valid_from,
    a.valid_to
from history a
join history b
    on a.provider_id = b.provider_id
    and a.valid_from <> b.valid_from
    and a.valid_from < b.valid_to
    and b.valid_from < a.valid_to
