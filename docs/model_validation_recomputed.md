# Recomputed Model Validation Evidence

This file is generated from exported validation artifacts and can be recreated with `python scripts/generate_model_evidence.py`.

## Validation Metrics

| Metric | Value | Interpretation |
| --- | --- | --- |
| Validation rows | 118,108 | Time-based holdout population. |
| Validation fraud baseline | 3.44% | Base precision before model ranking. |
| ROC-AUC | 0.9134 | Ranking power across thresholds. |
| Average precision | 0.5354 | Imbalance-aware model quality. |
| Brier score | 0.0636 | Probability calibration error; lower is better. |
| Expected calibration error | 14.52% | Weighted score-to-observed-rate gap across deciles. |
| KS statistic | 67.32% | Maximum separation between fraud and legitimate score distributions. |
| Top decile lift | 7.12x | Fraud concentration in the highest-score decile. |
| Operating threshold | 0.6767 | p95 validation score threshold. |
| Precision at threshold | 40.13% | Threshold-flagged transactions that are fraud. |
| Recall at threshold | 58.32% | Fraud labels captured by the selected threshold policy. |
| False-positive rate | 3.10% | Legitimate validation transactions flagged by the selected threshold. |
| Workload share | 5.00% | Share of validation transactions flagged by the selected threshold. |

## Holdout Stability Windows

| Window | Rows | Fraud rate | ROC-AUC | Average precision |
| --- | --- | --- | --- | --- |
| Holdout window 1 | 29,527 | 3.32% | 0.9145 | 0.5274 |
| Holdout window 2 | 29,527 | 2.95% | 0.9196 | 0.5499 |
| Holdout window 3 | 29,527 | 3.54% | 0.9033 | 0.5034 |
| Holdout window 4 | 29,527 | 3.96% | 0.9166 | 0.5608 |

## Calibration by Score Decile

| Score decile | Rows | Average score | Observed fraud rate | Calibration gap |
| --- | --- | --- | --- | --- |
| 1 | 11,811 | 1.42% | 0.04% | -1.38% |
| 2 | 11,811 | 2.90% | 0.23% | -2.67% |
| 3 | 11,811 | 4.39% | 0.28% | -4.11% |
| 4 | 11,810 | 6.20% | 0.33% | -5.87% |
| 5 | 11,811 | 8.46% | 0.58% | -7.88% |
| 6 | 11,811 | 11.46% | 0.74% | -10.72% |
| 7 | 11,810 | 15.70% | 1.14% | -14.55% |
| 8 | 11,811 | 22.54% | 2.00% | -20.55% |
| 9 | 11,811 | 36.07% | 4.56% | -31.51% |
| 10 | 11,811 | 70.46% | 24.51% | -45.95% |

## Feature Family Evidence

| Feature family | Feature count | Total importance | Top feature |
| --- | --- | --- | --- |
| Vesta engineered V | 339 | 8,193 | V313 |
| Timedelta D | 17 | 5,283 | D15 |
| Card | 6 | 4,657 | card1 |
| Counting C | 14 | 3,694 | C13 |
| Core transaction | 3 | 2,779 | TransactionDT |
| Identity id | 31 | 2,706 | id_02 |
| Address | 2 | 1,379 | addr1 |
| Email | 2 | 999 | P_emaildomain |
| Match M | 9 | 971 | M5 |
| Distance | 2 | 839 | dist1 |

## Governance Note

The model is suitable for analytical threshold policy and fraud prioritization. It should not be used as an autonomous decline engine without calibrated probabilities, production decision logs, model-risk approval, and bank-specific cost validation.
