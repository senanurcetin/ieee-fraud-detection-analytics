select
    table_name,
    column_name,
    column_family,
    row_count,
    missing_count,
    missing_rate
from {{ source('raw', 'feature_missingness') }}
