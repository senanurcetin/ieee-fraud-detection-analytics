with daily as (
    select
        sum(transaction_count) as total_transactions,
        sum(fraud_count) as fraud_transactions
    from {{ ref('mart_daily_stats') }}
),

base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as fraud_transactions
    from {{ ref('int_features') }}
)

select *
from daily
cross join base
where daily.total_transactions != base.total_transactions
   or daily.fraud_transactions != base.fraud_transactions
