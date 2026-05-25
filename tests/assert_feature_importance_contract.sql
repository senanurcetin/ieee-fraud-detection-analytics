with feature_quality as (
    select
        count(*) as row_count,
        count(distinct feature) as distinct_feature_count,
        min(importance) as min_importance,
        min(importance_rank) as min_rank,
        max(importance_rank) as max_rank
    from {{ ref('rpt_feature_importance') }}
)

select *
from feature_quality
where row_count < 15
   or distinct_feature_count != row_count
   or min_importance <= 0
   or min_rank != 1
   or max_rank < 15
