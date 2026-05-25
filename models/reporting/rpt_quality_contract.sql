select
    'raw.train_transaction' as object_name,
    590540 as expected_rows,
    (select count(*) from {{ source('raw', 'train_transaction') }}) as actual_rows,
    case when (select count(*) from {{ source('raw', 'train_transaction') }}) = 590540 then 'PASS' else 'FAIL' end as status
union all
select
    'raw.train_identity',
    144233,
    (select count(*) from {{ source('raw', 'train_identity') }}),
    case when (select count(*) from {{ source('raw', 'train_identity') }}) = 144233 then 'PASS' else 'FAIL' end
union all
select
    'raw.test_transaction',
    506691,
    (select count(*) from {{ source('raw', 'test_transaction') }}),
    case when (select count(*) from {{ source('raw', 'test_transaction') }}) = 506691 then 'PASS' else 'FAIL' end
union all
select
    'raw.test_identity',
    141907,
    (select count(*) from {{ source('raw', 'test_identity') }}),
    case when (select count(*) from {{ source('raw', 'test_identity') }}) = 141907 then 'PASS' else 'FAIL' end
union all
select
    'reporting.fact_train_transactions',
    590540,
    (select count(*) from {{ ref('fact_train_transactions') }}),
    case when (select count(*) from {{ ref('fact_train_transactions') }}) = 590540 then 'PASS' else 'FAIL' end
union all
select
    'reporting.rpt_executive_kpis',
    1,
    (select count(*) from {{ ref('rpt_executive_kpis') }}),
    case when (select count(*) from {{ ref('rpt_executive_kpis') }}) = 1 then 'PASS' else 'FAIL' end
