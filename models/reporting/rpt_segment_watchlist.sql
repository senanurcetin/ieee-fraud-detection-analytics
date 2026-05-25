with segments as (
    select
        'Product' as segment_family,
        product_cd as segment_name,
        transaction_count,
        fraud_count,
        fraud_rate,
        baseline_fraud_rate,
        lift,
        transaction_share,
        fraud_share,
        avg_transaction_amount
    from {{ ref('rpt_product_risk') }}

    union all

    select
        'Identity' as segment_family,
        identity_segment as segment_name,
        transaction_count,
        fraud_count,
        fraud_rate,
        baseline_fraud_rate,
        lift,
        transaction_share,
        fraud_share,
        null as avg_transaction_amount
    from {{ ref('rpt_identity_risk') }}

    union all

    select
        'Amount band' as segment_family,
        amount_band as segment_name,
        transaction_count,
        fraud_count,
        fraud_rate,
        baseline_fraud_rate,
        lift,
        transaction_share,
        fraud_share,
        avg_transaction_amount
    from {{ ref('rpt_amount_bands') }}

    union all

    select
        'Email domain' as segment_family,
        purchaser_email_group as segment_name,
        transaction_count,
        fraud_count,
        fraud_rate,
        baseline_fraud_rate,
        lift,
        transaction_share,
        fraud_share,
        avg_transaction_amount
    from {{ ref('rpt_email_domain_risk') }}

    union all

    select
        'Payment' as segment_family,
        concat(card_network, ' / ', card_type) as segment_name,
        transaction_count,
        fraud_count,
        fraud_rate,
        baseline_fraud_rate,
        lift,
        transaction_share,
        fraud_share,
        avg_transaction_amount
    from {{ ref('rpt_payment_heatmap') }}
),

scored as (
    select
        *,
        (coalesce(fraud_share, 0) * 0.45)
        + (coalesce(lift, 0) * 0.35)
        + (coalesce(transaction_share, 0) * 0.20) as priority_score
    from segments
    where transaction_count >= 1000
),

ranked as (
    select
        *,
        row_number() over (
            order by priority_score desc, fraud_share desc, lift desc, transaction_count desc
        ) as watchlist_rank
    from scored
)

select
    watchlist_rank,
    segment_family,
    segment_name,
    transaction_count,
    fraud_count,
    fraud_rate,
    baseline_fraud_rate,
    lift,
    transaction_share,
    fraud_share,
    avg_transaction_amount,
    priority_score,
    case
        when fraud_share >= 0.20 and lift >= 1.50 then 'Critical'
        when fraud_share >= 0.10 and lift >= 1.20 then 'High'
        when lift >= 1.10 then 'Monitor'
        else 'Normal'
    end as risk_priority,
    case
        when fraud_share >= 0.20 and lift >= 1.50 then 'Immediate segment review and rule calibration'
        when fraud_share >= 0.10 and lift >= 1.20 then 'Prioritize in the daily operations queue'
        when lift >= 1.10 then 'Monitor weekly trend and volume'
        else 'Standard reporting'
    end as recommended_action
from ranked
where watchlist_rank <= 20
order by watchlist_rank
