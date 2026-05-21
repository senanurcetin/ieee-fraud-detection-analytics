select
    transaction_hour,
    relative_hour_window,
    amount_decimal_group,
    transaction_count,
    fraud_count,
    fraud_rate,
    baseline_fraud_rate,
    lift,
    transaction_share,
    avg_transaction_amount
from {{ ref('mart_time_amount_signals') }}
