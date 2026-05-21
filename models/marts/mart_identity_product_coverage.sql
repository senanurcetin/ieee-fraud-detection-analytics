with base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud_count,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

product_identity as (
    select
        product_cd_clean as product_cd,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        sum(has_identity) as transactions_with_identity,
        {{ fp_avg_rate('has_identity') }} as identity_coverage_rate,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(case when has_identity = 1 then {{ fp_float('is_fraud') }} end) as fraud_rate_with_identity,
        avg(case when has_identity = 0 then {{ fp_float('is_fraud') }} end) as fraud_rate_without_identity
    from {{ ref('int_features') }}
    group by 1
)

select
    p.product_cd,
    p.transaction_count,
    p.fraud_count,
    p.transactions_with_identity,
    p.identity_coverage_rate,
    p.fraud_rate,
    p.fraud_rate_with_identity,
    p.fraud_rate_without_identity,
    p.fraud_rate / nullif(base.baseline_fraud_rate, 0) as fraud_lift,
    {{ fp_float('p.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('p.fraud_count') }} / nullif({{ fp_float('base.total_fraud_count') }}, 0) as fraud_share
from product_identity as p
cross join base
order by p.identity_coverage_rate desc, p.fraud_rate desc
