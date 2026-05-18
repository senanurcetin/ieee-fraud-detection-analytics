with base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud_count,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

banded as (
    select
        amount_band,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(transaction_amount) as avg_transaction_amount,
        sum(transaction_amount) as total_transaction_amount
    from {{ ref('int_features') }}
    group by 1
)

select
    b.amount_band,
    b.transaction_count,
    b.fraud_count,
    b.fraud_rate,
    base.baseline_fraud_rate,
    b.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    {{ fp_float('b.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('b.fraud_count') }} / nullif({{ fp_float('base.total_fraud_count') }}, 0) as fraud_share,
    b.avg_transaction_amount,
    b.total_transaction_amount
from banded as b
cross join base
order by b.amount_band
