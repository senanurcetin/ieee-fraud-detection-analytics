# Model Validation Evidence

## Validation Design

The model is evaluated with a chronological holdout:

- Training window: first 80% of train transactions by `TransactionDT`.
- Validation window: final 20% of train transactions by `TransactionDT`.

The project does not use random k-fold validation because random splits can leak temporal fraud patterns and overstate model quality in this dataset.

## Core Metrics

| Metric | Value | Interpretation |
|---|---:|---|
| ROC-AUC | 0.9167 | Ranking quality across thresholds |
| Average precision / AUC-PR proxy | 0.5308 | More relevant than accuracy for 3.5% fraud prevalence |
| Validation fraud baseline | 3.44% | Precision baseline for the holdout set |
| Top 10% validation score lift | 7.24x | Top-score decile fraud rate vs. validation baseline |
| High + Critical threshold precision | 40.4% | Validation precision at the p95 train-score threshold |
| High + Critical threshold recall | 59.4% | Validation fraud capture at the p95 train-score threshold |
| High + Critical threshold false-positive rate | 3.12% | Legitimate validation transactions sent to review |
| High + Critical threshold workload share | 5.06% | Share of validation transactions reviewed |

The same risk-band policy on the full training window captures 78.3% of fraud labels at 5.0% review workload. The validation metrics above are stricter and should be used when discussing generalization.

## Precision-Recall Curve

![Precision-recall curve](assets/precision_recall_curve.svg)

## Class Imbalance Treatment

The fraud rate is approximately 3.5%, so accuracy is not used as a success metric. The model and reporting layer use:

- ROC-AUC for ranking quality.
- Average precision / PR behavior for imbalance-aware evaluation.
- Review workload share to connect model thresholds to analyst capacity.
- Precision, recall, and false-positive rate at operating thresholds.
- Lift to explain concentration in the highest-score population.

## Cross-Validation Position

Current implementation:

- Single chronological holdout using the final 20% of `TransactionDT`.
- This is leakage-safer than random k-fold and aligns with fraud monitoring chronology.

Recommended next experiment:

- Add expanding-window time-based cross-validation.
- Report mean and standard deviation for ROC-AUC, AUC-PR, recall, false-positive rate, and lift.
- Compare against the current single-holdout result before changing model policy.
