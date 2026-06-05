-- SCD Type 2 history of the provider fraud label, derived from the
-- snap_provider_fraud snapshot. One row per (provider_id, validity window):
-- when a provider's is_potential_fraud value changes, the old row is closed
-- (valid_to set) and a new current row opens. Answers "when was this provider
-- first flagged / when did the flag change?".
select
    provider_id,
    is_potential_fraud,
    dbt_valid_from              as valid_from,
    dbt_valid_to               as valid_to,
    (dbt_valid_to is null)     as is_current
from {{ ref('snap_provider_fraud') }}
