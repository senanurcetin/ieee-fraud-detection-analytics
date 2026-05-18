select
    transaction_day,
    transaction_week,
    count(*) as transaction_count,
    sum(is_fraud) as fraud_count,
    avg(is_fraud::double) as fraud_rate,
    avg(transaction_amount) as avg_transaction_amount,
    median(transaction_amount) as median_transaction_amount,
    quantile_cont(transaction_amount, 0.95) as p95_transaction_amount
from {{ ref('int_features') }}
group by 1, 2
order by 1
