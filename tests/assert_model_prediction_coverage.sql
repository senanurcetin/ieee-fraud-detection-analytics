with predictions as (
    select
        split,
        count(*) as prediction_count
    from {{ ref('mart_model_predictions') }}
    group by 1
),

expected as (
    select 'train' as split, count(*) as expected_count from {{ source('raw', 'train_transaction') }}
    union all
    select 'test' as split, count(*) as expected_count from {{ source('raw', 'test_transaction') }}
),

joined as (
    select
        expected.split,
        expected.expected_count,
        coalesce(predictions.prediction_count, 0) as prediction_count
    from expected
    left join predictions
        on expected.split = predictions.split
)

select *
from joined
where expected_count != prediction_count
