with summary as (
    select * from {{ ref('mart_fraud_summary') }}
),

base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as fraud_transactions
    from {{ ref('int_features') }}
)

select
    summary.total_transactions as summary_total_transactions,
    base.total_transactions as base_total_transactions,
    summary.fraud_transactions as summary_fraud_transactions,
    base.fraud_transactions as base_fraud_transactions
from summary
cross join base
where summary.total_transactions != base.total_transactions
   or summary.fraud_transactions != base.fraud_transactions
