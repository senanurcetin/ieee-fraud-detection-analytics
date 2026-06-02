with base as (
    select
        is_fraud,
        address_proxy_status,
        distance_proxy_band
    from {{ ref('fact_train_transactions') }}
),

portfolio as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud,
        avg({{ fp_float('is_fraud') }}) as baseline_fraud_rate
    from base
),

proxy_segments as (
    select
        'Address proxy' as proxy_family,
        address_proxy_status as proxy_segment,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count
    from base
    group by address_proxy_status

    union all

    select
        'Distance proxy' as proxy_family,
        distance_proxy_band as proxy_segment,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count
    from base
    group by distance_proxy_band
)

select
    s.proxy_family,
    s.proxy_segment,
    s.transaction_count,
    s.fraud_count,
    1.0 * s.fraud_count / nullif(s.transaction_count, 0) as fraud_rate,
    p.baseline_fraud_rate,
    (1.0 * s.fraud_count / nullif(s.transaction_count, 0)) / nullif(p.baseline_fraud_rate, 0) as lift,
    1.0 * s.transaction_count / nullif(p.total_transactions, 0) as transaction_share,
    1.0 * s.fraud_count / nullif(p.total_fraud, 0) as fraud_share
from proxy_segments as s
cross join portfolio as p
order by lift desc, fraud_share desc
