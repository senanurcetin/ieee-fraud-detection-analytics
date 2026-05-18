with fact as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as fraud_transactions
    from {{ ref('fact_train_transactions') }}
),

base as (
    select
        count(*) as total_transactions,
        sum(is_fraud) as fraud_transactions
    from {{ ref('int_features') }}
)

select *
from fact
cross join base
where fact.total_transactions != base.total_transactions
   or fact.fraud_transactions != base.fraud_transactions
