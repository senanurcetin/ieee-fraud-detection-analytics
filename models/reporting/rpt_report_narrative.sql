select
    1 as page_order,
    'Executive Overview' as page_name,
    'Fraud is a low-frequency risk, but it concentrates sharply in a small number of segments.' as executive_message,
    'Product C, identity coverage, and critical model bands are the primary executive risk signals.' as analytical_focus,
    'Critical and high-risk bands should be prioritized in the operational review queue.' as recommended_action
union all
select
    2,
    'Segment Explorer',
    'Risk is not distributed uniformly across product, identity, and device cuts.',
    'Product and identity lift metrics make concentration visible for business stakeholders.',
    'High-lift segments should have dedicated monitoring and control rules.'
union all
select
    3,
    'Amount and Time Signals',
    'Fraud behavior is non-linear across amount and relative time dimensions.',
    'Amount bands, daily drift, and moving averages should be interpreted together.',
    'Periods with drift flags should trigger capacity and rule-set review.'
union all
select
    4,
    'Payment and Email Segments',
    'Payment type and email domain groups create explainable operational segments.',
    'Card network, card type, and purchaser email groups should be evaluated with volume and fraud share.',
    'High-volume, high-lift email and payment segments should be added to the watchlist.'
union all
select
    5,
    'Model Operations',
    'Model scores are a prioritization layer, not an autonomous decision mechanism.',
    'Risk-band lift, fraud capture, and feature importance explain the model business value.',
    'Critical and High bands should feed manual review, additional verification, or post-transaction monitoring.'
union all
select
    6,
    'Data Trust',
    'Data quality and lineage are the reliability foundation of the fraud report.',
    'Missingness, dbt tests, and layered BigQuery architecture should be presented together.',
    'Every refresh should pass dbt build, row-count, and reconciliation checks before presentation.'
