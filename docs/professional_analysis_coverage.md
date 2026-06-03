# Professional Fraud Analysis Coverage

This matrix translates the analyst workplan into concrete dashboard evidence, dbt outputs, and executive interpretation. It is intended for portfolio review and stakeholder walkthroughs.

## Coverage Matrix

| Analysis area | Business question | Dashboard evidence | Primary output |
|---|---|---|---|
| Data reliability | Are raw, mart, and dashboard populations reconciled? | Supporting Visuals / documentation | Row-count contract, duplicate protection, missingness profile, readiness gate. |
| Executive summary | What is the size of the risk problem? | Executive Fraud Overview | Baseline fraud rate, fraud concentration, policy capture, cost exposure, risk-band exposure. |
| Segment concentration | Where does fraud cluster? | Executive Fraud Overview / drill-through | Product risk, segment lift, fraud share, Pareto, comparable nested cuts. |
| Identity coverage | Is identity availability a risk signal? | Customer Risk Analysis | Identity-present versus identity-missing fraud rates and product identity matrix in Supporting Visuals. |
| Amount analysis | Do amount bands and amount decimals change fraud behavior? | Transaction Amount Analysis | Amount band risk, fraud exposure by amount, product x amount heatmap, amount diagnostics in Supporting Visuals. |
| Relative time analysis | Does risk move across elapsed time windows? | Fraud Trend Analysis / Behavioral Pattern Analysis | Relative day drift, relative hour fraud pattern, time-window monitoring signal. |
| Payment and email | Which card and email cuts are analytically useful? | Customer Risk Analysis | Full-width payment x email heatmap, email risk ranking, payment/email nested drill-through. |
| Masked proxy analysis | Do address and distance proxy fields add signal? | Masked Address & Distance Analysis | Proxy segment risk, fraud share versus volume, product x proxy heatmap, address/distance caveat. |
| Feature engineering | Which signals power the model and where is missingness structural? | Feature Importance Analysis | Feature importance, feature family treemap, missingness versus importance, masked-feature caveat. |
| ML performance | Is the model strong enough for review prioritization? | Model Performance Analysis | Time-based validation, ROC-AUC, average precision, top-decile lift, feature importance recap. |
| Threshold operations | Which score threshold balances capture and workload? | Model Performance Analysis | Threshold curve, selected-threshold capture, precision, workload, confusion matrix. |
| Business impact | What is the operational and financial tradeoff? | Model Performance Analysis / Key Insights & Recommendations | False-positive review cost, missed fraud exposure, net benefit proxy, review policy. |
| Presentation readiness | Is the public report defensible? | Production validation docs | KPI dictionary, methodology notes, analysis coverage matrix, release gates. |

## Defensible Hypotheses

1. Fraud is low at the portfolio level but concentrated in a manageable set of segments.
2. Product, identity, payment, and email fields create meaningful fraud separation.
3. TransactionDT must be interpreted as relative elapsed time, not as a real calendar timestamp.
4. Identity availability is both a coverage metric and a behavioral risk signal.
5. Model scores should prioritize analytical review and threshold policy, not automate customer decline.
6. The strongest decision uses fraud rate, lift, fraud share, workload, precision, and capture together.

## Analyst Interpretation Standard

- Never use baseline fraud rate alone to make an operational recommendation.
- Use lift to identify intensity and fraud share to identify operational materiality.
- Treat masked features as statistical evidence, not confirmed business definitions.
- Explain thresholds through workload, capture, precision, false-positive burden, and missed exposure.
- Keep row-count reconciliation and readiness checks as release gates before presentation.
