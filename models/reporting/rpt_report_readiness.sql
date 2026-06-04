with checks as (
    select
        'DATA_001' as check_id,
        'Raw train transaction row count' as check_name,
        '590540' as expected_value,
        {{ fp_string('(select count(*) from ' ~ source('raw', 'train_transaction') ~ ')') }} as actual_value,
        case when (select count(*) from {{ source('raw', 'train_transaction') }}) = 590540 then 'PASS' else 'FAIL' end as status,
        'Data reliability' as readiness_area

    union all

    select
        'DATA_002',
        'Web dashboard fact row count',
        '590540',
        {{ fp_string('(select count(*) from ' ~ ref('fact_train_transactions') ~ ')') }},
        case when (select count(*) from {{ ref('fact_train_transactions') }}) = 590540 then 'PASS' else 'FAIL' end,
        'Data reliability'

    union all

    select
        'STORY_001',
        'Report narrative coverage',
        '9',
        {{ fp_string('(select count(*) from ' ~ ref('rpt_report_narrative') ~ ')') }},
        case when (select count(*) from {{ ref('rpt_report_narrative') }}) = 9 then 'PASS' else 'FAIL' end,
        'Executive presentation'

    union all

    select
        'RISK_001',
        'Segment watchlist coverage',
        '>=10',
        {{ fp_string('(select count(*) from ' ~ ref('rpt_segment_watchlist') ~ ')') }},
        case when (select count(*) from {{ ref('rpt_segment_watchlist') }}) >= 10 then 'PASS' else 'FAIL' end,
        'Risk analytics'

    union all

    select
        'MODEL_001',
        'Risk band policy strategy',
        '4',
        {{ fp_string('(select count(*) from ' ~ ref('rpt_review_strategy') ~ ')') }},
        case when (select count(*) from {{ ref('rpt_review_strategy') }}) = 4 then 'PASS' else 'FAIL' end,
        'Model evidence'

    union all

    select
        'MODEL_002',
        'Reporting threshold simulation',
        '>=10',
        {{ fp_string('(select count(*) from ' ~ ref('rpt_threshold_simulation') ~ ')') }},
        case when (select count(*) from {{ ref('rpt_threshold_simulation') }}) >= 10 then 'PASS' else 'FAIL' end,
        'Model evidence'

    union all

    select
        'MODEL_003',
        'Validation threshold simulation',
        '>=10',
        {{ fp_string('(select count(*) from ' ~ ref('rpt_validation_threshold_simulation') ~ ')') }},
        case when (select count(*) from {{ ref('rpt_validation_threshold_simulation') }}) >= 10 then 'PASS' else 'FAIL' end,
        'Model evidence'

    union all

    select
        'MODEL_004',
        'Segment model performance',
        '>=10',
        {{ fp_string('(select count(*) from ' ~ ref('rpt_segment_model_performance') ~ ')') }},
        case when (select count(*) from {{ ref('rpt_segment_model_performance') }}) >= 10 then 'PASS' else 'FAIL' end,
        'Model evidence'
)

select
    check_id,
    check_name,
    expected_value,
    actual_value,
    status,
    readiness_area,
    case
        when status = 'PASS' then 'Ready for presentation'
        else 'Action required'
    end as readiness_result
from checks
order by check_id
