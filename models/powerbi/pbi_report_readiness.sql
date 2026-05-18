with checks as (
    select
        'DATA_001' as check_id,
        'Raw train transaction satır sayısı' as check_name,
        '590540' as expected_value,
        {{ fp_string('(select count(*) from ' ~ source('raw', 'train_transaction') ~ ')') }} as actual_value,
        case when (select count(*) from {{ source('raw', 'train_transaction') }}) = 590540 then 'PASS' else 'FAIL' end as status,
        'Veri Güvenilirliği' as readiness_area

    union all

    select
        'DATA_002',
        'Power BI fact satır sayısı',
        '590540',
        {{ fp_string('(select count(*) from ' ~ ref('fact_train_transactions') ~ ')') }},
        case when (select count(*) from {{ ref('fact_train_transactions') }}) = 590540 then 'PASS' else 'FAIL' end,
        'Veri Güvenilirliği'

    union all

    select
        'STORY_001',
        'Rapor sayfa anlatısı',
        '6',
        {{ fp_string('(select count(*) from ' ~ ref('pbi_report_narrative') ~ ')') }},
        case when (select count(*) from {{ ref('pbi_report_narrative') }}) = 6 then 'PASS' else 'FAIL' end,
        'Yönetici Sunumu'

    union all

    select
        'RISK_001',
        'Segment izleme listesi kapsamı',
        '>=10',
        {{ fp_string('(select count(*) from ' ~ ref('pbi_segment_watchlist') ~ ')') }},
        case when (select count(*) from {{ ref('pbi_segment_watchlist') }}) >= 10 then 'PASS' else 'FAIL' end,
        'Risk Analitiği'

    union all

    select
        'MODEL_001',
        'Risk bandı operasyon stratejisi',
        '4',
        {{ fp_string('(select count(*) from ' ~ ref('pbi_review_strategy') ~ ')') }},
        case when (select count(*) from {{ ref('pbi_review_strategy') }}) = 4 then 'PASS' else 'FAIL' end,
        'Model Operasyon'

    union all

    select
        'MODEL_002',
        'Threshold simülasyonu',
        '>=10',
        {{ fp_string('(select count(*) from ' ~ ref('pbi_threshold_simulation') ~ ')') }},
        case when (select count(*) from {{ ref('pbi_threshold_simulation') }}) >= 10 then 'PASS' else 'FAIL' end,
        'Model Operasyon'
)

select
    check_id,
    check_name,
    expected_value,
    actual_value,
    status,
    readiness_area,
    case
        when status = 'PASS' then 'Teslime hazır'
        else 'Aksiyon gerekli'
    end as readiness_result
from checks
order by check_id
