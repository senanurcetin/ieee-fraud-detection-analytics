-- Calibration of the model score against observed outcomes on the holdout.
--
-- The classifier is fitted with class_weight="balanced", which upweights the
-- 3.5% positive class by roughly 28 to 1. That is a deliberate choice for
-- ranking quality, and it works: the ranking metrics are strong. It also means
-- the outputs are not probabilities. They are systematically inflated, so the
-- score should be read as a rank, never as "this transaction is 70% likely to
-- be fraud".
--
-- Publishing the measurement rather than the assumption: this model reports the
-- reliability curve by score decile, the Brier score, and the Brier score a
-- constant base-rate prediction would achieve.

with scored as (
    select
        actual_is_fraud,
        predicted_fraud_probability,
        ntile(10) over (order by predicted_fraud_probability) as score_decile
    from {{ source('raw', 'validation_predictions') }}
    where predicted_fraud_probability is not null
),

overall as (
    select
        count(*) as holdout_transactions,
        {{ fp_avg_rate('actual_is_fraud') }} as holdout_baseline_rate,
        avg(predicted_fraud_probability) as holdout_mean_predicted,
        avg(power(predicted_fraud_probability - {{ fp_float('actual_is_fraud') }}, 2)) as brier_score
    from scored
),

bins as (
    select
        score_decile,
        count(*) as transaction_count,
        avg(predicted_fraud_probability) as mean_predicted_probability,
        {{ fp_avg_rate('actual_is_fraud') }} as observed_fraud_rate
    from scored
    group by 1
)

select
    b.score_decile,
    b.transaction_count,
    b.mean_predicted_probability,
    b.observed_fraud_rate,
    b.mean_predicted_probability - b.observed_fraud_rate as calibration_gap,
    o.holdout_transactions,
    o.holdout_baseline_rate,
    o.holdout_mean_predicted,
    -- How far the mean score sits from the outcome it is meant to describe.
    o.holdout_mean_predicted / nullif(o.holdout_baseline_rate, 0) as mean_overprediction_ratio,
    o.brier_score,
    -- A constant base-rate forecast scores base * (1 - base). When the model
    -- loses to that, its scores carry ranking information but no probability.
    o.holdout_baseline_rate * (1 - o.holdout_baseline_rate) as baseline_brier_score,
    -- Expected calibration error: bin-weighted mean absolute gap.
    sum(b.transaction_count * abs(b.mean_predicted_probability - b.observed_fraud_rate)) over ()
        / nullif(sum(b.transaction_count) over (), 0) as expected_calibration_error
from bins as b
cross join overall as o
order by b.score_decile
