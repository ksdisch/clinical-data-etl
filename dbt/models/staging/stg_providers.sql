with source as (

    select * from {{ source('raw', 'providers') }}

)

select
    "Provider"  as provider_id,
    case "PotentialFraud"
        when 'Yes' then true
        when 'No'  then false
        else null
    end         as is_potential_fraud

from source
