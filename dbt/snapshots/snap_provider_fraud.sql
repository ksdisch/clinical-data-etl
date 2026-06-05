{% snapshot snap_provider_fraud %}

{{
    config(
        target_schema='snapshots',
        unique_key='provider_id',
        strategy='check',
        check_cols=['is_potential_fraud'],
        invalidate_hard_deletes=True
    )
}}

-- SCD Type 2 history of the provider fraud label. Reads the raw source directly
-- (not stg_providers) so the snapshot is decoupled from the model DAG and can run
-- before `dbt run`. The Yes/No -> boolean mapping mirrors stg_providers.
select
    "Provider" as provider_id,
    case "PotentialFraud"
        when 'Yes' then true
        when 'No'  then false
        else null
    end as is_potential_fraud
from {{ source('raw', 'providers') }}

{% endsnapshot %}
