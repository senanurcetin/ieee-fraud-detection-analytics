with base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud_count,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

identity_risk as (
    select
        has_identity,
        case when has_identity = 1 then 'Identity present' else 'Identity missing' end as identity_segment,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate
    from {{ ref('int_features') }}
    group by 1, 2
)

select
    i.has_identity,
    i.identity_segment,
    i.transaction_count,
    i.fraud_count,
    i.fraud_rate,
    base.baseline_fraud_rate,
    i.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    {{ fp_float('i.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('i.fraud_count') }} / nullif({{ fp_float('base.total_fraud_count') }}, 0) as fraud_share
from identity_risk as i
cross join base
order by i.has_identity desc
