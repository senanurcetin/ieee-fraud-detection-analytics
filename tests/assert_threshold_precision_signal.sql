with thresholds as (
    select
        max(case when score_threshold <= 0.03 then precision_rate end) as broad_precision,
        max(case when score_threshold >= 0.20 then precision_rate end) as strict_precision,
        max(case when score_threshold <= 0.03 then workload_share end) as broad_workload,
        max(case when score_threshold >= 0.20 then workload_share end) as strict_workload
    from {{ ref('rpt_threshold_simulation') }}
)

select *
from thresholds
where strict_precision <= broad_precision
   or strict_workload >= broad_workload
