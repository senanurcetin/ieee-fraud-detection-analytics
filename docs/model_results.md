# Model Results

## Objective

The model is designed as a threshold-policy evidence layer. It is not positioned as an automated decline engine. The practical question is: can the model rank transactions well enough to concentrate fraud labels into measurable risk bands?

## Validation Design

The validation split is time-based. Transactions are ordered by `TransactionDT`, and the last 20% of the training window is used as the validation holdout. This avoids the leakage risk that a random k-fold split would introduce in a fraud dataset with temporal behavior.

`TransactionDT` is treated as elapsed seconds from a reference point, not as a real calendar timestamp.

## Class Imbalance

The dataset has a low fraud prevalence of approximately 3.5%. Accuracy is therefore not used as a decision metric because a trivial "always legitimate" classifier would look strong while providing no fraud detection value.

The project reports:

- ROC-AUC for ranking quality.
- Average precision / AUC-PR proxy for imbalanced-class performance.
- Precision, recall, and false-positive rate at operating thresholds.
- Workload share to connect model thresholds to business capacity.
- Lift to show whether high-score bands concentrate fraud.

## Validation Metrics

| Metric | Value | Interpretation |
|---|---:|---|
| ROC-AUC | 0.9134 | Strong ranking quality across thresholds |
| Average precision / AUC-PR proxy | 0.5354 | Materially above the 3.44% validation fraud baseline |
| Validation fraud baseline | 3.44% | Base precision before model prioritization |
| Top 10% validation score lift | 7.12x | Top decile fraud rate versus validation baseline |
| Top 5% validation precision | 40.13% | Share of top-score validation transactions that are fraud |
| Top 5% validation recall | 58.32% | Share of fraud labels captured by the top 5% score band |
| Top 5% validation false-positive rate | 3.10% | Legitimate validation transactions flagged by the top 5% score band |
| Top 5% validation workload share | 5.00% | Share of validation transactions in the focused score band |
| Fixed 0.50 threshold precision | 25.68% | Precision when using a fixed probability threshold |
| Fixed 0.50 threshold recall | 69.78% | Fraud capture when using a fixed probability threshold |
| Registry feature count | 425 | Active registry scope after V1-V339 missingness-filtered expansion |
| Rolling CV mean ROC-AUC | 0.9100 | Three expanding windows show stable ranking performance |

## Model Registry

The project now exposes model governance metadata in two places:

- JSON artifact: `docs/model_registry.json`
- API endpoint: `/api/enterprise/model-registry`

The registry records `training_date`, `model_version`, V-feature scope, feature count, holdout metrics, rolling cross-validation windows, and the model-use policy. The current registry version is `lightgbm-v2-v339-missingness-filtered`.

## Operating Point

The dashboard presents two threshold-policy operating points:

- The top 5% validation score band is the focused control scenario: 40.13% precision, 58.32% recall, and 5.00% workload.
- The fixed 0.50 threshold is the higher-capture scenario: 25.68% precision, 69.78% recall, and 9.35% workload.
- Both options raise fraud concentration far above the 3.44% validation baseline.

This threshold should be recalibrated if analyst capacity, fraud cost, customer friction cost, or product mix changes.

## Feature Importance

The reporting layer exposes feature importance through `rpt_feature_importance`. The strongest signal families include card attributes, transaction timing, transaction amount, anonymous engineered Vesta features, email domain, distance, and identity fields.

The model uses masked variables as statistical signals only. It does not assign unsupported business meanings to anonymized fields such as V1-V339, C1-C14, D1-D15, M1-M9, or id columns.

Top 10 feature importance snapshot:

| Rank | Feature | Feature family | Importance |
|---:|---|---|---:|
| 1 | `card1` | Card | 1,844 |
| 2 | `card2` | Card | 1,525 |
| 3 | `addr1` | Address | 1,333 |
| 4 | `TransactionDT` | Core transaction | 1,329 |
| 5 | `TransactionAmt` | Core transaction | 1,300 |
| 6 | `C13` | Counting C | 856 |
| 7 | `D15` | Timedelta D | 830 |
| 8 | `D2` | Timedelta D | 699 |
| 9 | `P_emaildomain` | Email | 692 |
| 10 | `dist1` | Distance | 658 |

## Explainability Artifacts

- Precision-recall curve: `docs/assets/precision_recall_curve.svg`
- Feature importance export: `docs/assets/model_feature_importance.png`
- Feature contribution summary export: `docs/assets/model_shap_summary.png`
- Transaction explanation endpoint: `/api/enterprise/cases/{transaction_id}/explain`

## Business Interpretation

The model creates value by turning a low-prevalence fraud problem into threshold-policy evidence. Instead of treating the full transaction population equally, the model identifies narrow high-score bands where fraud concentration is materially higher than baseline.

Recommended use:

| Risk band | Operational use |
|---|---|
| Critical | Critical threshold-policy focus |
| High | High-priority analytical review band |
| Elevated | Sample-based control check and monitoring |
| Low | Baseline monitoring |

## Remaining Model Improvements

- Test calibrated probability outputs if the model will be used for cost-sensitive thresholding.
- Add cost-weighted threshold optimization using false-negative cost, false-positive review cost, and customer-friction assumptions.
- Add analyst feedback outcomes before any production-style decision automation.

