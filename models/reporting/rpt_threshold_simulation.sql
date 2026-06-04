with thresholds as (
    select 0.01 as score_threshold union all
    select 0.02 union all
    select 0.03 union all
    select 0.04 union all
    select 0.05 union all
    select 0.06 union all
    select 0.07 union all
    select 0.08 union all
    select 0.09 union all
    select 0.10 union all
    select 0.15 union all
    select 0.20 union all
    select 0.25 union all
    select 0.30 union all
    select 0.40 union all
    select 0.50
),

base as (
    select
        count(*) as total_transactions,
        sum(coalesce(actual_is_fraud, 0)) as total_observed_fraud
    from {{ ref('mart_model_predictions') }}
    where split = 'train'
),

scored as (
    select
        t.score_threshold,
        count(*) as review_count,
        sum(coalesce(p.actual_is_fraud, 0)) as captured_fraud_count
    from thresholds as t
    inner join {{ ref('mart_model_predictions') }} as p
        on p.split = 'train'
        and p.predicted_fraud_probability >= t.score_threshold
    group by 1
)

select
    s.score_threshold,
    s.review_count,
    s.captured_fraud_count,
    {{ fp_float('s.review_count') }} / nullif({{ fp_float('b.total_transactions') }}, 0) as workload_share,
    {{ fp_float('s.captured_fraud_count') }} / nullif({{ fp_float('b.total_observed_fraud') }}, 0) as fraud_capture_rate,
    {{ fp_float('s.captured_fraud_count') }} / nullif({{ fp_float('s.review_count') }}, 0) as precision_rate,
    case
        when s.score_threshold <= 0.03 then 'Broad monitoring'
        when s.score_threshold <= 0.08 then 'Balanced threshold policy'
        when s.score_threshold <= 0.20 then 'Focused risk policy'
        else 'Narrow critical policy'
    end as operating_mode
from scored as s
cross join base as b
order by s.score_threshold
