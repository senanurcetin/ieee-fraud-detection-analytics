select
    count(*) as total_transactions,
    sum(is_fraud) as fraud_transactions,
    count(*) - sum(is_fraud) as legitimate_transactions,
    {{ fp_avg_rate('is_fraud') }} as fraud_rate,
    sum(has_identity) as transactions_with_identity,
    {{ fp_avg_rate('has_identity') }} as identity_coverage_rate,
    avg(transaction_amount) as avg_transaction_amount,
    {{ fp_percentile('transaction_amount', 0.50) }} as median_transaction_amount,
    {{ fp_percentile('transaction_amount', 0.95) }} as p95_transaction_amount,
    max(transaction_day) as observed_days,
    count(distinct product_cd_clean) as product_count,
    count(distinct purchaser_email_group) as purchaser_email_group_count
from {{ ref('int_features') }}
