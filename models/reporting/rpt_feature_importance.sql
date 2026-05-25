select
    feature,
    feature_family,
    importance,
    row_number() over (order by importance desc, feature) as importance_rank
from {{ source('raw', 'feature_importance') }}
where importance > 0
order by importance_rank
