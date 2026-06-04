select
    score_threshold,
    evidence_scope,
    review_count,
    captured_fraud_count,
    false_positive_count,
    false_negative_count,
    workload_share,
    fraud_capture_rate,
    precision_rate,
    false_positive_rate,
    operating_mode
from {{ source('raw', 'validation_threshold_simulation') }}
order by score_threshold
