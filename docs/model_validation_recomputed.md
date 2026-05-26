# Recomputed Model Validation Evidence

This file is generated from exported validation artifacts and can be recreated with `python scripts/generate_model_evidence.py`.

## Validation Metrics

| Metric | Value | Interpretation |
| --- | --- | --- |
| Validation rows | 118,108 | Time-based holdout population. |
| Validation fraud baseline | 3.44% | Base precision before model ranking. |
| ROC-AUC | 0.9167 | Ranking power across thresholds. |
| Average precision | 0.5308 | Imbalance-aware model quality. |
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
| Holdout window 1 | 29,527 | 3.32% | 0.9140 | 0.5232 |
| Holdout window 2 | 29,527 | 2.95% | 0.9239 | 0.5505 |
| Holdout window 3 | 29,527 | 3.54% | 0.9062 | 0.4972 |
| Holdout window 4 | 29,527 | 3.96% | 0.9222 | 0.5520 |

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
| Timedelta D | 17 | 6,326 | D2 |
| Card | 6 | 5,039 | card1 |
| Vesta engineered V | 120 | 4,668 | V62 |
| Counting C | 14 | 4,220 | C13 |
| Identity id | 31 | 3,215 | id_20 |
| Core transaction | 3 | 3,159 | TransactionDT |
| Address | 2 | 1,608 | addr1 |
| Email | 2 | 1,211 | P_emaildomain |
| Match M | 9 | 1,120 | M4 |
| Distance | 2 | 934 | dist1 |

## Governance Note

The model is suitable for prioritizing analyst review queues. It should not be used as an autonomous decline engine without calibrated probabilities, production decision logs, model-risk approval, and bank-specific cost validation.
