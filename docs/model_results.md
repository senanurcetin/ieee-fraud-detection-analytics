# Model Results

## Objective

The model is designed as a review-prioritization layer for fraud operations. It is not positioned as an automated decline engine. The practical question is: can the model rank transactions well enough to concentrate fraud labels into a manageable review queue?

## Validation Design

The validation split is time-based. Transactions are ordered by `TransactionDT`, and the last 20% of the training window is used as the validation holdout. This avoids the leakage risk that a random k-fold split would introduce in a fraud dataset with temporal behavior.

`TransactionDT` is treated as elapsed seconds from a reference point, not as a real calendar timestamp.

## Class Imbalance

The dataset has a low fraud prevalence of approximately 3.5%. Accuracy is therefore not used as a decision metric because a trivial "always legitimate" classifier would look strong while providing no fraud detection value.

The project reports:

- ROC-AUC for ranking quality.
- Average precision / AUC-PR proxy for imbalanced-class performance.
- Precision, recall, and false-positive rate at operating thresholds.
- Review workload share to connect model thresholds to analyst capacity.
- Lift to show whether high-score bands concentrate fraud.

## Validation Metrics

| Metric | Value | Interpretation |
|---|---:|---|
| ROC-AUC | 0.9167 | Strong ranking quality across thresholds |
| Average precision / AUC-PR proxy | 0.5308 | Materially above the 3.44% validation fraud baseline |
| Validation fraud baseline | 3.44% | Base precision before model prioritization |
| Top 10% validation score lift | 7.24x | Top decile fraud rate versus validation baseline |
| High + Critical precision | 40.4% | Share of reviewed High + Critical transactions that are fraud |
| High + Critical recall | 59.4% | Share of fraud labels captured by the High + Critical queue |
| High + Critical false-positive rate | 3.12% | Legitimate validation transactions sent to review |
| High + Critical workload share | 5.06% | Share of validation transactions requiring review |

## Operating Point

The recommended operating point is the High + Critical queue. It is a pragmatic balance between fraud capture and review capacity:

- It reviews a small share of total transactions.
- It captures a majority of fraud labels in the validation holdout.
- It improves analyst efficiency by raising the reviewed population's fraud rate far above baseline.

This threshold should be recalibrated if analyst capacity, fraud cost, customer friction cost, or product mix changes.

## Feature Importance

The reporting layer exposes feature importance through `pbi_feature_importance`. The strongest signal families include card attributes, transaction timing, transaction amount, anonymous engineered Vesta features, email domain, distance, and identity fields.

The model uses masked variables as statistical signals only. It does not assign unsupported business meanings to anonymized fields such as V1-V339, C1-C14, D1-D15, M1-M9, or id columns.

Top 10 feature importance snapshot:

| Rank | Feature | Feature family | Importance |
|---:|---|---|---:|
| 1 | `card1` | Card | 1,917 |
| 2 | `card2` | Card | 1,743 |
| 3 | `addr1` | Address | 1,566 |
| 4 | `TransactionDT` | Core transaction | 1,546 |
| 5 | `TransactionAmt` | Core transaction | 1,408 |
| 6 | `C13` | Counting C | 944 |
| 7 | `D2` | Timedelta D | 943 |
| 8 | `D15` | Timedelta D | 876 |
| 9 | `P_emaildomain` | Email | 755 |
| 10 | `dist1` | Distance | 696 |

## Explainability Artifacts

- Precision-recall curve: `docs/assets/precision_recall_curve.svg`
- Feature importance export: `powerbi/assets/05_feature_importance.png`
- SHAP summary export: `powerbi/assets/26_shap_summary.png`

## Business Interpretation

The model creates value by turning a low-prevalence fraud problem into an ordered review queue. Instead of asking operations to inspect the full transaction population, the model identifies a narrow set of high-risk transactions where fraud concentration is materially higher than baseline.

Recommended use:

| Risk band | Operational use |
|---|---|
| Critical | Immediate review or additional verification |
| High | Same-day priority review |
| Elevated | Sample-based manual control and weekly monitoring |
| Low | Standard automated monitoring |

## Next Experiments

- Expand the V-family feature scope beyond the baseline V1-V120 subset and compare AUC-PR, recall, false-positive rate, lift, and runtime.
- Test calibrated probability outputs if the model will be used for cost-sensitive thresholding.
- Add rolling validation windows to monitor concept drift.
- Add cost-weighted threshold optimization using false-negative cost, false-positive review cost, and customer-friction assumptions.
