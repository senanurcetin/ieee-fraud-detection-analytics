with expected as (
    select 'train' as split, 'Low' as risk_band
    union all select 'train', 'Elevated'
    union all select 'train', 'High'
    union all select 'train', 'Critical'
    union all select 'test', 'Low'
    union all select 'test', 'Elevated'
    union all select 'test', 'High'
    union all select 'test', 'Critical'
),

actual as (
    select distinct split, risk_band
    from {{ ref('mart_risk_band_stats') }}
),

missing as (
    select expected.*
    from expected
    left join actual
        on expected.split = actual.split
        and expected.risk_band = actual.risk_band
    where actual.risk_band is null
)

select *
from missing
