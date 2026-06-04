with validation as (
    select
        transaction_id,
        actual_is_fraud,
        predicted_fraud_probability,
        case when predicted_fraud_probability >= 0.50 then 1 else 0 end as predicted_positive
    from {{ source('raw', 'validation_predictions') }}
),

base as (
    select
        f.transaction_id,
        v.actual_is_fraud,
        v.predicted_fraud_probability,
        v.predicted_positive,
        coalesce(f.product_cd, 'Unknown') as product_segment,
        coalesce(f.amount_band, 'Unknown') as amount_segment,
        case when f.has_identity = 1 then 'Identity present' else 'Identity missing' end as identity_segment,
        coalesce(f.purchaser_email_group, 'Unknown') as email_segment,
        concat(coalesce(f.card_network, 'Unknown'), ' / ', coalesce(f.card_type, 'Unknown')) as payment_segment
    from validation as v
    inner join {{ ref('fact_train_transactions') }} as f
        on v.transaction_id = f.transaction_id
),

segments as (
    select
        'Product' as segment_family,
        product_segment as segment_name,
        transaction_id,
        actual_is_fraud,
        predicted_fraud_probability,
        predicted_positive
    from base

    union all

    select
        'Amount band' as segment_family,
        amount_segment as segment_name,
        transaction_id,
        actual_is_fraud,
        predicted_fraud_probability,
        predicted_positive
    from base

    union all

    select
        'Identity' as segment_family,
        identity_segment as segment_name,
        transaction_id,
        actual_is_fraud,
        predicted_fraud_probability,
        predicted_positive
    from base

    union all

    select
        'Email domain' as segment_family,
        email_segment as segment_name,
        transaction_id,
        actual_is_fraud,
        predicted_fraud_probability,
        predicted_positive
    from base

    union all

    select
        'Payment' as segment_family,
        payment_segment as segment_name,
        transaction_id,
        actual_is_fraud,
        predicted_fraud_probability,
        predicted_positive
    from base
),

scored as (
    select
        segment_family,
        segment_name,
        count(*) as validation_transactions,
        sum(actual_is_fraud) as validation_fraud_count,
        sum(predicted_positive) as review_count,
        sum(case when predicted_positive = 1 and actual_is_fraud = 1 then 1 else 0 end) as captured_fraud_count,
        sum(case when predicted_positive = 1 and actual_is_fraud = 0 then 1 else 0 end) as false_positive_count,
        sum(case when predicted_positive = 0 and actual_is_fraud = 1 then 1 else 0 end) as false_negative_count
    from segments
    group by 1, 2
)

select
    segment_family,
    segment_name,
    validation_transactions,
    validation_fraud_count,
    review_count,
    captured_fraud_count,
    false_positive_count,
    false_negative_count,
    {{ fp_float('validation_fraud_count') }} / nullif({{ fp_float('validation_transactions') }}, 0) as validation_fraud_rate,
    {{ fp_float('review_count') }} / nullif({{ fp_float('validation_transactions') }}, 0) as workload_share,
    {{ fp_float('captured_fraud_count') }} / nullif({{ fp_float('review_count') }}, 0) as precision_rate,
    {{ fp_float('captured_fraud_count') }} / nullif({{ fp_float('validation_fraud_count') }}, 0) as recall_rate,
    case
        when validation_transactions < 1000 then 'Low support'
        when validation_transactions < 5000 then 'Medium support'
        else 'High support'
    end as support_level
from scored
where validation_transactions > 0
order by segment_family, precision_rate desc, validation_fraud_count desc
