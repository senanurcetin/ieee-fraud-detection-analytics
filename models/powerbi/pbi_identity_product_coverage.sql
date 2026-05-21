select
    product_cd,
    transaction_count,
    fraud_count,
    transactions_with_identity,
    identity_coverage_rate,
    fraud_rate,
    fraud_rate_with_identity,
    fraud_rate_without_identity,
    fraud_lift,
    transaction_share,
    fraud_share
from {{ ref('mart_identity_product_coverage') }}
