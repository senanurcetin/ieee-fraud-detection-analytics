with base as (
    select
        split,
        count(*) as total_transactions,
        sum(coalesce(actual_is_fraud, 0)) as total_observed_fraud_count,
        {{ fp_avg_rate('actual_is_fraud') }} as baseline_observed_fraud_rate
    from {{ ref('mart_model_predictions') }}
    group by 1
),

bands as (
    select
        split,
        risk_band,
        count(*) as transaction_count,
        avg(predicted_fraud_probability) as avg_predicted_probability,
        sum(coalesce(actual_is_fraud, 0)) as observed_fraud_count,
        {{ fp_avg_rate('actual_is_fraud') }} as observed_fraud_rate
    from {{ ref('mart_model_predictions') }}
    group by 1, 2
)

select
    b.split,
    b.risk_band,
    case b.risk_band
        when 'Critical' then 1
        when 'High' then 2
        when 'Elevated' then 3
        else 4
    end as band_rank,
    case b.risk_band
        when 'Critical' then 'Acil inceleme'
        when 'High' then 'Öncelikli inceleme'
        when 'Elevated' then 'Kuyruk izleme'
        else 'Standart izleme'
    end as review_priority,
    b.transaction_count,
    b.avg_predicted_probability,
    b.observed_fraud_count,
    b.observed_fraud_rate,
    base.baseline_observed_fraud_rate,
    b.observed_fraud_rate / nullif(base.baseline_observed_fraud_rate, 0) as lift,
    {{ fp_float('b.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('b.observed_fraud_count') }} / nullif({{ fp_float('base.total_observed_fraud_count') }}, 0) as expected_fraud_capture
from bands as b
left join base
    on b.split = base.split
order by b.split, band_rank
