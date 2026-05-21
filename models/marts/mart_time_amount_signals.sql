with base as (
    select
        count(*) as total_transactions,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

signals as (
    select
        transaction_hour,
        case
            when transaction_hour between 0 and 5 then 'Night'
            when transaction_hour between 6 and 11 then 'Morning'
            when transaction_hour between 12 and 17 then 'Afternoon'
            else 'Evening'
        end as relative_hour_window,
        is_round_amount,
        case when is_round_amount = 1 then 'Round amount' else 'Cent amount' end as amount_decimal_group,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(transaction_amount) as avg_transaction_amount
    from {{ ref('int_features') }}
    group by 1, 2, 3, 4
)

select
    s.transaction_hour,
    s.relative_hour_window,
    s.is_round_amount,
    s.amount_decimal_group,
    s.transaction_count,
    s.fraud_count,
    s.fraud_rate,
    base.baseline_fraud_rate,
    s.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    {{ fp_float('s.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    s.avg_transaction_amount
from signals as s
cross join base
order by s.transaction_hour, s.is_round_amount desc
