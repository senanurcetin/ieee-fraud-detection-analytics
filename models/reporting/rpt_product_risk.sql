with base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud_count,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

product_risk as (
    select
        product_cd_clean as product_cd,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(transaction_amount) as avg_transaction_amount
    from {{ ref('int_features') }}
    group by 1
)

select
    p.product_cd,
    p.transaction_count,
    p.fraud_count,
    p.fraud_rate,
    base.baseline_fraud_rate,
    p.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    {{ fp_float('p.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('p.fraud_count') }} / nullif({{ fp_float('base.total_fraud_count') }}, 0) as fraud_share,
    p.avg_transaction_amount
from product_risk as p
cross join base
order by p.fraud_rate desc
