with base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as total_fraud_count,
        {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

email as (
    select
        purchaser_email_group,
        case
            when purchaser_email_group = 'Unknown' then 'Unknown'
            when purchaser_email_group = 'anonymous.com' then 'Privacy masked'
            when purchaser_email_group in ('gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com', 'comcast.net') then 'Mainstream consumer'
            else 'Long-tail / other'
        end as purchaser_email_risk_group,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(transaction_amount) as avg_transaction_amount
    from {{ ref('int_features') }}
    group by 1
)

select
    e.purchaser_email_group,
    e.purchaser_email_risk_group,
    e.transaction_count,
    e.fraud_count,
    e.fraud_rate,
    base.baseline_fraud_rate,
    e.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    {{ fp_float('e.transaction_count') }} / nullif({{ fp_float('base.total_transactions') }}, 0) as transaction_share,
    {{ fp_float('e.fraud_count') }} / nullif({{ fp_float('base.total_fraud_count') }}, 0) as fraud_share,
    e.avg_transaction_amount
from email as e
cross join base
order by e.transaction_count desc
