# Executive Summary

## Core Finding

Fraud is rare in the IEEE-CIS portfolio, but it is highly concentrated. Product, identity coverage, card attributes, email domain, amount band, and model risk band produce materially different fraud rates. The project converts these patterns into a governed analytical pipeline and an executive live web analytics dashboard.

## Portfolio Metrics

| Metric | Value |
|---|---:|
| Total transactions | 590,540 |
| Fraud-labeled transactions | 20,663 |
| Baseline fraud rate | 3.50% |
| Total transaction amount | $79.7M |
| Fraud-labeled amount | $3.08M |
| Identity coverage rate | 24.42% |
| Validation ROC-AUC | 0.9134 |
| Validation average precision | 0.5354 |

## Management Recommendation

Use the model as a threshold-policy evidence layer, not as an automated decline engine. The recommended focused operating point is the top 5% validation score band:

- Flags 5.00% of validation transactions.
- Captures 58.32% of validation fraud labels.
- Delivers 40.13% precision versus a 3.44% validation baseline.
- Provides a defensible starting policy; the fixed 0.50 threshold can be used when higher capture is more important than workload.

## Business Action

Start with a controlled analytical policy pilot:

1. Use Critical and High score bands as the first policy focus.
2. Monitor Product C, identity-present transactions, and high-risk payment/email combinations separately.
3. Track threshold precision, recall, and workload before any automated decision use.
4. Recalibrate thresholds after real decision outcomes and cost inputs are collected.

