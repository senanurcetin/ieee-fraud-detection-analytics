select
    split,
    risk_band,
    count(*) as transaction_count,
    avg(predicted_fraud_probability) as avg_predicted_probability,
    sum(coalesce(actual_is_fraud, 0)) as observed_fraud_count,
    {{ fp_avg_rate('actual_is_fraud') }} as observed_fraud_rate
from {{ ref('mart_model_predictions') }}
group by 1, 2
order by 1, avg_predicted_probability desc
