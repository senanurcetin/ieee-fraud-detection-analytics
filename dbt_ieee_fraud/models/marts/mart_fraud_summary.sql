select
    count(*) as total_transactions,
    sum(is_fraud) as fraud_transactions,
    count(*) - sum(is_fraud) as legitimate_transactions,
    avg(is_fraud::double) as fraud_rate,
    sum(has_identity) as transactions_with_identity,
    avg(has_identity::double) as identity_coverage_rate,
    avg(transaction_amount) as avg_transaction_amount,
    median(transaction_amount) as median_transaction_amount,
    quantile_cont(transaction_amount, 0.95) as p95_transaction_amount,
    max(transaction_day) as observed_days,
    count(distinct product_cd_clean) as product_count,
    count(distinct purchaser_email_group) as purchaser_email_group_count
from {{ ref('int_features') }}
