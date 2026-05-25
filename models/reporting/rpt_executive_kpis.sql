with summary as (
    select * from {{ ref('mart_fraud_summary') }}
),

product_c as (
    select
        product_cd_clean as product_cd,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate
    from {{ ref('int_features') }}
    where product_cd_clean = 'C'
    group by 1
),

identity as (
    select
        has_identity,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate
    from {{ ref('int_features') }}
    group by 1
),

critical_risk as (
    select
        transaction_count,
        observed_fraud_count,
        observed_fraud_rate,
        lift
    from {{ ref('mart_risk_band_stats') }}
    where split = 'train'
      and risk_band = 'Critical'
)

select
    s.total_transactions,
    s.fraud_transactions,
    s.legitimate_transactions,
    s.fraud_rate,
    s.identity_coverage_rate,
    s.avg_transaction_amount,
    s.median_transaction_amount,
    s.p95_transaction_amount,
    pc.transaction_count as product_c_transactions,
    pc.fraud_rate as product_c_fraud_rate,
    pc.fraud_rate / nullif(s.fraud_rate, 0) as product_c_lift,
    iw.fraud_rate as with_identity_fraud_rate,
    iwo.fraud_rate as without_identity_fraud_rate,
    iw.fraud_rate / nullif(iwo.fraud_rate, 0) as identity_lift,
    cr.transaction_count as critical_risk_transactions,
    cr.observed_fraud_count as critical_risk_fraud_count,
    cr.observed_fraud_rate as critical_risk_fraud_rate,
    cr.lift as critical_risk_lift
from summary as s
left join product_c as pc
    on pc.product_cd = 'C'
left join identity as iw
    on iw.has_identity = 1
left join identity as iwo
    on iwo.has_identity = 0
left join critical_risk as cr
    on 1 = 1
