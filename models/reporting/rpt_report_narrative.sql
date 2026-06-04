select
    1 as page_order,
    'Executive Fraud Overview' as page_name,
    'Fraud is low-frequency at portfolio level, but concentrated enough to manage through targeted controls.' as executive_message,
    'Start with total exposure, fraud trend, risk-band exposure, and top segment concentration.' as analytical_focus,
    'Use executive KPIs to frame the story, then prove concentration with segment and model evidence.' as recommended_action
union all
select
    2,
    'Fraud Trend Analysis',
    'Relative TransactionDT movement reveals behavioral drift, not calendar seasonality.',
    'Read fraud-rate movement together with transaction volume and drift flags.',
    'Use peak relative days as investigation windows before changing a threshold.'
union all
select
    3,
    'Transaction Amount Analysis',
    'Amount risk is non-linear: frequency risk and financial exposure can point to different bands.',
    'Compare amount-band fraud rate, fraud exposure, and product-by-amount heatmaps.',
    'Use amount-specific controls only after validating product and payment context.'
union all
select
    4,
    'Customer Risk Analysis',
    'IEEE-CIS does not expose real customers, so identity, device, email, card, and product fields are customer-behavior proxies.',
    'Use identity lift, email-domain risk, and payment-by-email heatmaps to find nested behavior segments.',
    'Do not compare unrelated segments; drill from proxy family into related subsegments.'
union all
select
    5,
    'Masked Address & Distance Analysis',
    'Address and distance fields are masked proxy signals, not geography.',
    'Use proxy fraud rate, fraud share versus volume share, and product-by-proxy heatmaps.',
    'Treat high-lift proxy segments as monitoring candidates only with product and amount context.'
union all
select
    6,
    'Behavioral Pattern Analysis',
    'Fraud behavior clusters across relative hour, payment behavior, amount pattern, and model score.',
    'Use relative-hour fraud pattern and behavior signal strength before interpreting outlier diagnostics.',
    'Keep behavior findings as monitoring inputs, not calendar-time claims.'
union all
select
    7,
    'Feature Importance Analysis',
    'The model separates fraud using multiple feature families, not a single variable.',
    'Show feature importance, family-level importance, and missingness-versus-importance together.',
    'Frame masked features as observational model drivers rather than confirmed business definitions.'
union all
select
    8,
    'Model Performance Analysis',
    'Holdout validation proves ranking quality; reporting simulation shows how thresholds affect portfolio review volume.',
    'Separate ROC-AUC/PR-AUC validation evidence from train/reporting threshold simulation.',
    'Use the validation threshold table and segment model performance before recommending a policy.'
union all
select
    9,
    'Key Insights & Recommendations',
    'The business decision is segment-aware risk management, not one global fraud rule.',
    'Close with concentration, nested segmentation, model evidence, and data-quality limits.',
    'Pilot segment-specific monitoring, add valid enrichment only when real fields exist, and track calibration over time.'
