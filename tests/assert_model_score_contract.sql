select
    transaction_id,
    split,
    actual_is_fraud,
    predicted_fraud_probability,
    risk_band
from {{ ref('mart_model_predictions') }}
where predicted_fraud_probability is null
   or predicted_fraud_probability < 0
   or predicted_fraud_probability > 1
   or risk_band not in ('Critical', 'High', 'Elevated', 'Low')
   or (actual_is_fraud is not null and actual_is_fraud not in (0, 1))
