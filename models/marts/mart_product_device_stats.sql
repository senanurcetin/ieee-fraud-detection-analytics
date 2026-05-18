with base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud_count,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

segments as (
    select
        product_cd_clean as product_cd,
        device_type_clean as device_type,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(transaction_amount) as avg_transaction_amount,
        {{ fp_percentile('transaction_amount', 0.95) }} as p95_transaction_amount
    from {{ ref('int_features') }}
    group by 1, 2
    having count(*) >= 100
)

select
    s.product_cd,
    s.device_type,
    s.transaction_count,
    s.fraud_count,
    s.fraud_rate,
    base.baseline_fraud_rate,
    s.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    {{ fp_float('s.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('s.fraud_count') }} / nullif({{ fp_float('base.total_fraud_count') }}, 0) as fraud_share,
    s.avg_transaction_amount,
    s.p95_transaction_amount
from segments as s
cross join base
order by s.fraud_rate desc, s.transaction_count desc
