select
    score_threshold,
    review_count,
    captured_fraud_count,
    workload_share,
    fraud_capture_rate,
    precision_rate,
    operating_mode
from {{ ref('rpt_threshold_simulation') }}
where review_count < captured_fraud_count
   or workload_share < 0
   or workload_share > 1
   or fraud_capture_rate < 0
   or fraud_capture_rate > 1
   or precision_rate < 0
   or precision_rate > 1
   or operating_mode not in (
        'Broad monitoring',
        'Balanced threshold policy',
        'Focused risk policy',
        'Narrow critical policy'
    )
