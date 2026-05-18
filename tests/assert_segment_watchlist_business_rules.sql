with ranked as (
    select
        *,
        row_number() over (order by watchlist_rank) as expected_rank
    from {{ ref('pbi_segment_watchlist') }}
),

violations as (
    select *
    from ranked
    where watchlist_rank != expected_rank
       or transaction_count < 1000
       or coalesce(lift, -1) < 0
       or coalesce(priority_score, -1) < 0
       or risk_priority is null
       or recommended_action is null
       or trim(recommended_action) = ''
)

select *
from violations
