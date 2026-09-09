-- Risk band evidence on the time-based holdout.
--
-- mart_risk_band_stats reports the 'train' split, but the model is fit on the
-- first 80% of TransactionDT and then scores all 590,540 rows, so four fifths
-- of that split is in-sample. Reading band quality off it overstates the model:
-- the High band shows 44.59% there against 30.34% on transactions the model
-- never saw during fit.
--
-- The band cut points are recovered from the scored train split rather than
-- recomputed, so the holdout is partitioned by exactly the same thresholds.

with cuts as (
    select
        min(case when risk_band = 'Critical' then predicted_fraud_probability end) as critical_cut,
        min(case when risk_band = 'High' then predicted_fraud_probability end) as high_cut,
        min(case when risk_band = 'Elevated' then predicted_fraud_probability end) as elevated_cut
    from {{ ref('mart_model_predictions') }}
    where split = 'train'
),

banded as (
    select
        v.actual_is_fraud,
        v.predicted_fraud_probability,
        case
            when v.predicted_fraud_probability >= c.critical_cut then 'Critical'
            when v.predicted_fraud_probability >= c.high_cut then 'High'
            when v.predicted_fraud_probability >= c.elevated_cut then 'Elevated'
            else 'Low'
        end as risk_band
    from {{ source('raw', 'validation_predictions') }} as v
    cross join cuts as c
),

base as (
    select
        count(*) as total_transactions,
        sum(coalesce(actual_is_fraud, 0)) as total_observed_fraud_count,
        {{ fp_avg_rate('actual_is_fraud') }} as baseline_observed_fraud_rate
    from banded
),

bands as (
    select
        risk_band,
        count(*) as transaction_count,
        avg(predicted_fraud_probability) as avg_predicted_probability,
        sum(coalesce(actual_is_fraud, 0)) as observed_fraud_count,
        {{ fp_avg_rate('actual_is_fraud') }} as observed_fraud_rate
    from banded
    group by 1
)

select
    'validation' as split,
    b.risk_band,
    case b.risk_band
        when 'Critical' then 1
        when 'High' then 2
        when 'Elevated' then 3
        else 4
    end as band_rank,
    case b.risk_band
        when 'Critical' then 'Critical threshold focus'
        when 'High' then 'High-priority analytical band'
        when 'Elevated' then 'Sample-based control check'
        else 'Baseline monitoring'
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
cross join base
order by band_rank
