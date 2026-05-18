with counts as (
    select
        (select count(*) from {{ ref('stg_transactions') }}) as staging_count,
        (select count(*) from {{ source('raw', 'train_transaction') }}) as source_count
)

select *
from counts
where staging_count != source_count
