# Executive Summary

## Core Finding

Fraud is rare in the IEEE-CIS portfolio, but it is highly concentrated. Product, identity coverage, card attributes, email domain, amount band, and model risk band produce materially different fraud rates. The project converts these patterns into a governed analytical pipeline and an executive Power BI report.

## Portfolio Metrics

| Metric | Value |
|---|---:|
| Total transactions | 590,540 |
| Fraud-labeled transactions | 20,663 |
| Baseline fraud rate | 3.50% |
| Total transaction amount | $79.7M |
| Fraud-labeled amount | $3.08M |
| Identity coverage rate | 24.42% |
| Validation ROC-AUC | 0.9167 |
| Validation average precision | 0.5308 |

## Management Recommendation

Use the model as a review-prioritization layer, not as an automated decline engine. The recommended operating point is `High + Critical`:

- Reviews 5.0% of transactions.
- Captures 78.3% of fraud-labeled transactions in the training window.
- Delivers 54.8% precision and 0.645 F1.
- Captures $2.38M of the $3.08M fraud-labeled amount in the dataset.

## Business Action

Start with a controlled fraud-operations pilot:

1. Route `Critical` transactions to immediate review.
2. Route `High` transactions to same-day analyst review.
3. Monitor `Elevated` segments weekly for drift and emerging fraud patterns.
4. Recalibrate thresholds after analyst decision outcomes are collected.
