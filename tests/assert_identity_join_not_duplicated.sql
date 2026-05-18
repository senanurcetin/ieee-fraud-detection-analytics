select
    transaction_id,
    count(*) as duplicate_count
from {{ ref('int_fraud_joined') }}
group by 1
having count(*) > 1
