with ordered as (
    select
        score_threshold,
        workload_share,
        fraud_capture_rate,
        precision_rate,
        lag(workload_share) over (order by score_threshold) as previous_workload_share,
        lag(fraud_capture_rate) over (order by score_threshold) as previous_fraud_capture_rate
    from {{ ref('pbi_threshold_simulation') }}
),

violations as (
    select *
    from ordered
    where previous_workload_share is not null
      and (
        workload_share > previous_workload_share + 0.000001
        or fraud_capture_rate > previous_fraud_capture_rate + 0.000001
        or precision_rate < 0
        or precision_rate > 1
      )
)

select *
from violations
