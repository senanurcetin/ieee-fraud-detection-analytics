select
    transaction_day,
    transaction_week,
    count(*) as transaction_count,
    sum(is_fraud) as fraud_count,
    {{ fp_avg_rate('is_fraud') }} as fraud_rate,
    avg(transaction_amount) as avg_transaction_amount,
    {{ fp_percentile('transaction_amount', 0.50) }} as median_transaction_amount,
    {{ fp_percentile('transaction_amount', 0.95) }} as p95_transaction_amount
from {{ ref('int_features') }}
group by 1, 2
order by 1
