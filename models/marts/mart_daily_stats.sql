with base as (
    select {{ fp_avg_rate('is_fraud') }} as baseline_fraud_rate
    from {{ ref('int_features') }}
),

daily as (
    select
        transaction_day,
        transaction_week,
        count(*) as transaction_count,
        sum(is_fraud) as fraud_count,
        {{ fp_avg_rate('is_fraud') }} as fraud_rate,
        avg(transaction_amount) as avg_transaction_amount,
        {{ fp_percentile('transaction_amount', 0.50) }} as median_transaction_amount,
        {{ fp_percentile('transaction_amount', 0.95) }} as p95_transaction_amount
    from {{ ref('int_features') }}
    group by 1, 2
),

windowed as (
    select
        daily.*,
        avg(fraud_rate) over (
            order by transaction_day
            rows between 6 preceding and current row
        ) as fraud_rate_ma7,
        avg(transaction_count) over (
            order by transaction_day
            rows between 6 preceding and current row
        ) as transaction_count_ma7
    from daily
)

select
    w.transaction_day,
    w.transaction_week,
    w.transaction_count,
    w.fraud_count,
    w.fraud_rate,
    base.baseline_fraud_rate,
    w.fraud_rate / nullif(base.baseline_fraud_rate, 0) as lift,
    w.fraud_rate_ma7,
    w.transaction_count_ma7,
    case
        when w.fraud_rate_ma7 >= base.baseline_fraud_rate * 1.25 then 'Yüksek risk drift'
        when w.fraud_rate_ma7 <= base.baseline_fraud_rate * 0.75 then 'Düşük risk drift'
        else 'Normal bant'
    end as drift_flag,
    w.avg_transaction_amount,
    w.median_transaction_amount,
    w.p95_transaction_amount
from windowed as w
cross join base
order by w.transaction_day
