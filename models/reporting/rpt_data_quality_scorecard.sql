select
    table_name,
    column_family,
    count(*) as column_count,
    avg(missing_rate) as avg_missing_rate,
    max(missing_rate) as max_missing_rate,
    sum(missing_count) as total_missing_values,
    max(row_count) as row_count
from {{ ref('mart_feature_missingness') }}
group by 1, 2
order by avg_missing_rate desc
