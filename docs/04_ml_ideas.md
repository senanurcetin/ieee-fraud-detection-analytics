# 04 - ML Ideas

## Current Modeling Approach

The project uses a LightGBM binary classifier to rank transactions by fraud probability. The model is validated with a time-based holdout: transactions are ordered by `TransactionDT`, and the last 20% of the training window is used for validation.

This mirrors a real fraud-monitoring setting more closely than random k-fold validation because future-like observations are not allowed to leak into the training sample.

## Current Evidence

- ROC-AUC: 0.9134
- Average precision / AUC-PR proxy: 0.5354
- Validation baseline fraud rate: 3.44%
- Top 10% validation score lift: 7.12x
- Top 5% validation precision: 40.13%
- Top 5% validation recall: 58.32%
- Top 5% validation workload: 5.00%
- Fixed 0.50 threshold precision: 25.68%
- Fixed 0.50 threshold recall: 69.78%
- Feature count: 425
- Categorical feature count: 26

## Risk Bands

Predicted probabilities are converted into operational risk bands:

| Risk band | Intended use |
|---|---|
| Critical | Critical threshold-policy focus |
| High | High-priority analytical review band |
| Elevated | Sample-based control check and monitoring |
| Low | Baseline monitoring |

The bands simplify model consumption for analysts and executives. They should be recalibrated if portfolio mix, fraud cost, analyst capacity, or customer-friction assumptions change.

## Class Imbalance Strategy

The dataset has a fraud rate near 3.5%, so accuracy is not used as a decision metric. The project focuses on ranking, precision-recall behavior, lift, and workload share. Threshold decisions are evaluated against capacity and expected cost assumptions in the web dashboard.

## Explainability Strategy

The model uses masked features as statistical signals only. It does not assign unsupported business definitions to Vesta-masked columns such as V1-V339, C1-C14, D1-D15, M1-M9, or identity IDs.

Explainability artifacts:

- `docs/assets/model_feature_importance.png`
- `docs/assets/model_shap_summary.png`
- `docs/assets/precision_recall_curve.svg`

## Next ML Enhancements

1. Add rolling time-window validation to monitor model stability.
2. Compare calibrated probabilities against raw LightGBM scores for cost-sensitive thresholding.
3. Add model drift checks for product, email, amount-band, and risk-band distribution changes.
4. Track threshold performance by segment so the business can tune product, channel, and amount policies.
5. Store model version, feature list, validation metrics, and threshold definitions as machine-readable metadata.
6. Add a lightweight retraining trigger based on fraud-rate drift, feature drift, and threshold degradation.

