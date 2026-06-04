# Banking Business Impact

## Objective

The analytical objective is not only to predict fraud, but to convert model scores into transparent threshold-policy scenarios. The dashboard separates validation evidence from reporting-score segmentation so management can compare capture, workload, precision, and exposure.

## Portfolio Baseline

| Metric | Value |
|---|---:|
| Total transactions | 590,540 |
| Fraud-labeled transactions | 20,663 |
| Baseline fraud rate | 3.50% |
| Total transaction amount | $79.7M |
| Fraud-labeled amount | $3.08M |
| Average fraud-labeled amount | $149.24 |

## Validation Threshold Comparison

| Policy | Validation flagged volume | Workload share | Captured fraud labels | Precision | Recall | Business reading |
|---|---:|---:|---:|---:|---:|---:|
| Top 5% validation score band | 5,906 | 5.00% | 2,370 | 40.13% | 58.32% | Focused control band |
| Fixed 0.50 threshold | 11,043 | 9.35% | 2,836 | 25.68% | 69.78% | Higher-capture scenario |
| Top 10% validation score band | 11,811 | 10.00% | 2,895 | 24.51% | 71.24% | Broad monitoring scenario |

## Recommended Operating Point

The recommended executive story uses the top 5% validation score band as the focused threshold-policy baseline:

- It flags only 5.00% of validation transactions.
- It captures 58.32% of validation fraud labels.
- It keeps precision at 40.13%, far above the 3.44% validation baseline.
- The fixed 0.50 scenario is available when management prioritizes higher capture over workload.

## Threshold Decision Rule

The decision rule is intentionally operational, not purely statistical:

1. Start with the smallest threshold band that meets the target fraud-capture level.
2. Check that estimated flagged volume stays inside available review or control capacity.
3. If capacity is breached, raise the score threshold or add segment-specific gating.
4. If fraud capture is below the target, lower the threshold and offset workload through segment prioritization.
5. Do not use the model as an automatic decline engine until calibration, decision logging, and model-risk approval are in place.

The dashboard implements this rule client-side through capacity, false-positive review cost, and false-negative loss inputs.

## Financial Framing

The project separates measured dataset value from operational assumptions.

Measured dataset values:

- Fraud-labeled amount can be evaluated by selected score threshold and segment filters in the dashboard.
- False-positive burden is estimated from validation threshold precision and workload.

Illustrative operating assumptions for a banking presentation:

- Investigation cost per reviewed transaction: $3.00
- Preventable fraud share after business intervention: 60%
- Customer friction cost is monitored but not directly monetized in this portfolio version.

Illustrative impact:

- Preventable fraud value: selected threshold exposure * 60%
- Review operating cost: selected flagged volume * $3.00
- Net value before customer-friction adjustment is recalculated in the dashboard threshold simulator.

This is not presented as realized savings. It is a decision frame for prioritizing review capacity and for defining the next production pilot.

## Sensitivity Scenarios

| Scenario | Review cost assumption | Missed-fraud loss assumption | Management interpretation |
|---|---:|---:|---|
| Base pilot | $4 per false-positive review | $120 per missed fraud | Default weekly risk committee scenario. |
| Higher review cost | $8 per false-positive review | $120 per missed fraud | Tests whether analyst capacity or customer friction makes the selected threshold too expensive. |
| Higher fraud loss | $4 per false-positive review | $240 per missed fraud | Tests whether capture should be increased even if review volume rises. |
| Stress case | $8 per false-positive review | $240 per missed fraud | Defines the decision boundary before production pilot approval. |

These are scenario controls rather than accounting claims. They help management understand how the recommended threshold changes when operating assumptions change.

## False Positive / False Negative Interpretation

False positives are legitimate transactions flagged by the selected threshold. Their cost is analyst time, potential customer friction, and delayed approval. False negatives are fraud transactions left outside the selected threshold. Their cost is expected fraud loss and regulatory exposure. The selected policy intentionally accepts some false positives to materially reduce high-value false negatives.

## Next Decision

Before production deployment, the bank should calibrate the threshold with real cost inputs:

- Average fraud loss after recoveries
- Review team hourly cost and daily capacity
- Customer friction penalty for delayed approvals
- Required fraud capture target by product and channel

