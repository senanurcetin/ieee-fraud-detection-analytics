with ordered as (
    select
        split,
        risk_band,
        band_rank,
        observed_fraud_rate,
        avg_predicted_probability,
        lag(observed_fraud_rate) over (partition by split order by band_rank) as previous_observed_fraud_rate,
        lag(avg_predicted_probability) over (partition by split order by band_rank) as previous_avg_predicted_probability
    from {{ ref('mart_risk_band_stats') }}
    where observed_fraud_rate is not null
      and avg_predicted_probability is not null
),

violations as (
    select *
    from ordered
    where previous_observed_fraud_rate is not null
      and (
        observed_fraud_rate > previous_observed_fraud_rate + 0.000001
        or avg_predicted_probability > previous_avg_predicted_probability + 0.000001
      )
)

select *
from violations
