# Recomputed Model Validation Evidence

This file is generated from exported validation artifacts and can be recreated with `python scripts/generate_model_evidence.py`.

## Validation Metrics

| Metric | Value | Interpretation |
| --- | --- | --- |
| Validation rows | 118,108 | Time-based holdout population. |
| Validation fraud baseline | 3.44% | Base precision before model ranking. |
| ROC-AUC | 0.9139 | Ranking power across thresholds. |
| Average precision | 0.5370 | Imbalance-aware model quality. |
| Brier score | 0.0654 | Probability calibration error; lower is better. |
| Expected calibration error | 14.87% | Weighted score-to-observed-rate gap across deciles. |
| KS statistic | 67.81% | Maximum separation between fraud and legitimate score distributions. |
| Top decile lift | 7.24x | Fraud concentration in the highest-score decile. |
| Operating threshold | 0.6892 | p95 validation score threshold. |
| Precision at threshold | 40.72% | Reviewed transactions that are fraud. |
| Recall at threshold | 59.18% | Fraud labels captured by the queue. |
| False-positive rate | 3.07% | Legitimate transactions sent to review. |
| Workload share | 5.00% | Share of validation transactions reviewed. |

## Holdout Stability Windows

| Window | Rows | Fraud rate | ROC-AUC | Average precision |
| --- | --- | --- | --- | --- |
| Rolling window 1 | 118,108 | 3.75% | 0.8919 | 0.5522 |
| Rolling window 2 | 118,108 | 3.90% | 0.9239 | 0.5843 |
| Rolling window 3 | 118,108 | 3.44% | 0.9142 | 0.5220 |

## Calibration by Score Decile

| Score decile | Rows | Average score | Observed fraud rate | Calibration gap |
| --- | --- | --- | --- | --- |
| 1 | 11,811 | 1.46% | 0.06% | -1.40% |
| 2 | 11,811 | 3.03% | 0.18% | -2.86% |
| 3 | 11,811 | 4.51% | 0.21% | -4.30% |
| 4 | 11,810 | 6.26% | 0.32% | -5.93% |
| 5 | 11,811 | 8.53% | 0.48% | -8.05% |
| 6 | 11,811 | 11.59% | 0.75% | -10.84% |
| 7 | 11,810 | 16.02% | 1.28% | -14.74% |
| 8 | 11,811 | 23.08% | 1.90% | -21.18% |
| 9 | 11,811 | 37.22% | 4.32% | -32.91% |
| 10 | 11,811 | 71.36% | 24.91% | -46.45% |

## Feature Family Evidence

| Feature family | Feature count | Total importance | Top feature |
| --- | --- | --- | --- |
| Vesta engineered V | 339 | 8,254 | V310 |
| Timedelta D | 17 | 5,279 | D15 |
| Card | 6 | 4,653 | card1 |
| Counting C | 14 | 3,713 | C13 |
| Core transaction | 3 | 2,805 | TransactionDT |
| Identity id | 31 | 2,602 | id_02 |
| Address | 2 | 1,369 | addr1 |
| Email | 2 | 1,001 | P_emaildomain |
| Match M | 9 | 970 | M5 |
| Distance | 2 | 854 | dist1 |

## Governance Note

The model is suitable for prioritizing analyst review queues. It should not be used as an autonomous decline engine without calibrated probabilities, production decision logs, model-risk approval, and bank-specific cost validation.
