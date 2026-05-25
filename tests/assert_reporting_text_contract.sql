with invalid_values as (
    select 'segment_watchlist_priority' as contract_area, risk_priority as invalid_value
    from {{ ref('rpt_segment_watchlist') }}
    where risk_priority not in ('Critical', 'High', 'Monitor', 'Normal')

    union all

    select 'review_strategy_queue_policy', queue_policy
    from {{ ref('rpt_review_strategy') }}
    where queue_policy not in (
        'Real-time manual review queue',
        'Same-day priority review',
        'Sample-based manual control',
        'Automated monitoring'
    )

    union all

    select 'threshold_operating_mode', operating_mode
    from {{ ref('rpt_threshold_simulation') }}
    where operating_mode not in (
        'Broad monitoring',
        'Balanced operations',
        'Focused risk queue',
        'Narrow critical queue'
    )

    union all

    select 'report_readiness_result', readiness_result
    from {{ ref('rpt_report_readiness') }}
    where readiness_result not in ('Ready for presentation', 'Action required')

    union all

    select 'daily_drift_flag', drift_flag
    from {{ ref('rpt_daily_drift') }}
    where drift_flag not in ('High risk drift', 'Low risk drift', 'Normal band')
)

select *
from invalid_values
