select
    product_cd_clean as product_cd,
    device_type_clean as device_type,
    count(*) as transaction_count,
    sum(is_fraud) as fraud_count,
    {{ fp_avg_rate('is_fraud') }} as fraud_rate,
    avg(transaction_amount) as avg_transaction_amount,
    {{ fp_percentile('transaction_amount', 0.95) }} as p95_transaction_amount
from {{ ref('int_features') }}
group by 1, 2
having count(*) >= 100
order by fraud_rate desc, transaction_count desc
