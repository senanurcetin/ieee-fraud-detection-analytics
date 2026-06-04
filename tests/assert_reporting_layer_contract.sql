with contract_failures as (
    select 'quality_contract' as contract_area, count(*) as failure_count
    from {{ ref('rpt_quality_contract') }}
    where status != 'PASS'

    union all

    select 'report_readiness', count(*)
    from {{ ref('rpt_report_readiness') }}
    where status != 'PASS'

    union all

    select 'report_narrative_pages', case when count(*) = 9 then 0 else 1 end
    from {{ ref('rpt_report_narrative') }}

    union all

    select 'native_reporting_fact', case when count(*) = 590540 then 0 else 1 end
    from {{ ref('fact_train_transactions') }}
)

select *
from contract_failures
where failure_count > 0
