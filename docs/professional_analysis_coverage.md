# Professional Fraud Analysis Coverage

This matrix translates the analyst workplan into concrete dashboard evidence, dbt outputs, and executive interpretation. It is intended for portfolio review and stakeholder walkthroughs.

## Coverage Matrix

| Analysis area | Business question | Dashboard evidence | Primary output |
|---|---|---|---|
| Data reliability | Are raw, mart, and dashboard populations reconciled? | Model Operations appendix | Row-count contract, duplicate protection, missingness profile, readiness gate. |
| Executive summary | What is the size of the risk problem? | Executive Overview | Baseline fraud rate, fraud concentration, policy capture, cost exposure, Pareto, queue mix. |
| Segment concentration | Where does fraud cluster? | Executive Overview / Segment Lab | Product risk, segment lift, fraud share, Pareto, same-family comparison, operational watchlist. |
| Identity coverage | Is identity availability a risk signal? | Niche Signals | Identity-present versus identity-missing fraud rates and ProductCD coverage matrix. |
| Amount analysis | Do amount bands and amount decimals change fraud behavior? | Executive Overview / Niche Signals | Amount band risk, amount exposure bubbles, round versus cent amount pattern. |
| Relative time analysis | Does risk move across elapsed time windows? | Executive Overview / Niche Signals | Relative day drift, relative hour heatmap, time-window monitoring signal. |
| Payment and email | Which card and email cuts are operationally useful? | Niche Signals | Payment heatmap, card network/type risk, purchaser email domain risk. |
| Feature engineering | Which signals power the model and where is missingness structural? | Model Operations / Appendix | Feature importance, feature family treemap, missingness scorecard, masked-feature caveat. |
| ML performance | Is the model strong enough for review prioritization? | Model Operations | Time-based validation, ROC-AUC, average precision, top-decile lift, feature importance. |
| Threshold operations | Which score threshold balances capture and workload? | Model Operations | Threshold curve, selected-threshold capture, precision, workload, confusion matrix. |
| Business impact | What is the operational and financial tradeoff? | Model Operations | False-positive review cost, missed fraud exposure, capacity status, review policy. |
| Presentation readiness | Is the public report defensible? | Model Operations appendix | KPI dictionary, methodology notes, analysis coverage matrix, hypothesis register. |

## Defensible Hypotheses

1. Fraud is low at the portfolio level but concentrated in a manageable set of segments.
2. Product, identity, payment, and email fields create meaningful fraud separation.
3. TransactionDT must be interpreted as relative elapsed time, not as a real calendar timestamp.
4. Identity availability is both a coverage metric and a behavioral risk signal.
5. Model scores should prioritize analyst review queues, not automate customer decline.
6. The strongest decision uses fraud rate, lift, fraud share, workload, precision, and capture together.

## Analyst Interpretation Standard

- Never use baseline fraud rate alone to make an operational recommendation.
- Use lift to identify intensity and fraud share to identify operational materiality.
- Treat masked features as statistical evidence, not confirmed business definitions.
- Explain thresholds through workload, capture, precision, false-positive burden, and missed exposure.
- Keep row-count reconciliation and readiness checks as release gates before presentation.
