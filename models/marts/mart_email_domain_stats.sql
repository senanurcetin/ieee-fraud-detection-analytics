select
    purchaser_email_group,
    count(*) as transaction_count,
    sum(is_fraud) as fraud_count,
    {{ fp_avg_rate('is_fraud') }} as fraud_rate,
    avg(transaction_amount) as avg_transaction_amount
from {{ ref('int_features') }}
group by 1
order by transaction_count desc
