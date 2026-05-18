with violations as (
    select *
    from {{ ref('pbi_review_strategy') }}
    where risk_band not in ('Critical', 'High', 'Elevated', 'Low')
       or band_rank not between 1 and 4
       or review_priority is null
       or queue_policy is null
       or management_note is null
       or estimated_daily_review_volume < 0
       or observed_fraud_rate < 0
       or observed_fraud_rate > 1
       or transaction_share < 0
       or transaction_share > 1
       or expected_fraud_capture < 0
       or expected_fraud_capture > 1
)

select *
from violations
