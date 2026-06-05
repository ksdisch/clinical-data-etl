-- SCD2 invariant: every provider has exactly one current (open) version.
-- Returns providers violating that (test passes on zero rows).
select
    provider_id,
    count(*) filter (where is_current) as current_rows
from {{ ref('dim_provider_history') }}
group by provider_id
having count(*) filter (where is_current) <> 1
