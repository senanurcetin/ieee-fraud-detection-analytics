select
    transaction_id,
    split,
    actual_is_fraud,
    predicted_fraud_probability,
    risk_band
from {{ source('raw', 'ml_predictions') }}
