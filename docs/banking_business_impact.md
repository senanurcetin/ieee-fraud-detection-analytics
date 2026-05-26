# Banking Business Impact

## Objective

The analytical objective is not only to predict fraud, but to convert model scores into a review policy that can be operated by a fraud team. The recommended operating point is the `High + Critical` review queue because it balances fraud capture and analyst workload.

## Portfolio Baseline

| Metric | Value |
|---|---:|
| Total transactions | 590,540 |
| Fraud-labeled transactions | 20,663 |
| Baseline fraud rate | 3.50% |
| Total transaction amount | $79.7M |
| Fraud-labeled amount | $3.08M |
| Average fraud-labeled amount | $149.24 |

## Review Policy Comparison

| Policy | Review volume | Workload share | Captured fraud labels | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Critical only | 5,906 | 1.0% | 5,688 | 96.3% | 27.5% | 0.428 |
| High + Critical | 29,527 | 5.0% | 16,174 | 54.8% | 78.3% | 0.645 |
| Elevated + High + Critical | 118,108 | 20.0% | 19,726 | 16.7% | 95.5% | 0.284 |

## Recommended Operating Point

`High + Critical` is the recommended executive policy:

- It reviews only 5.0% of transactions.
- It captures 78.3% of fraud-labeled transactions in the training window.
- It keeps precision at 54.8%, which is high enough for a manual investigation queue.
- It avoids the operational overload caused by reviewing the broader `Elevated` band.

## Threshold Decision Rule

The decision rule is intentionally operational, not purely statistical:

1. Start with the smallest queue that meets the target fraud-capture level.
2. Check that estimated daily review volume stays inside analyst capacity.
3. If capacity is breached, raise the score threshold or restrict the queue to `High + Critical`.
4. If fraud capture is below the target, lower the threshold and offset workload through segment prioritization.
5. Do not use the model as an automatic decline engine until calibration, decision logging, and model-risk approval are in place.

The dashboard implements this rule client-side through capacity, false-positive review cost, and false-negative loss inputs.

## Financial Framing

The project separates measured dataset value from operational assumptions.

Measured dataset values:

- Fraud-labeled amount captured by `High + Critical`: $2.38M
- False-positive transaction count in `High + Critical`: 13,353

Illustrative operating assumptions for a banking presentation:

- Investigation cost per reviewed transaction: $3.00
- Preventable fraud share after manual review: 60%
- Customer friction cost is monitored but not directly monetized in this portfolio version.

Illustrative impact:

- Preventable fraud value: $2.38M * 60% = $1.43M
- Review operating cost: 29,527 * $3.00 = $88.6K
- Net value before customer-friction adjustment: approximately $1.34M

This is not presented as realized savings. It is a decision frame for prioritizing review capacity and for defining the next production pilot.

## Sensitivity Scenarios

| Scenario | Review cost assumption | Missed-fraud loss assumption | Management interpretation |
|---|---:|---:|---|
| Base pilot | $4 per false-positive review | $120 per missed fraud | Default weekly risk committee scenario. |
| Higher review cost | $8 per false-positive review | $120 per missed fraud | Tests whether analyst capacity or customer friction makes the queue too expensive. |
| Higher fraud loss | $4 per false-positive review | $240 per missed fraud | Tests whether capture should be increased even if review volume rises. |
| Stress case | $8 per false-positive review | $240 per missed fraud | Defines the decision boundary before production pilot approval. |

These are scenario controls rather than accounting claims. They help management understand how the recommended threshold changes when operating assumptions change.

## False Positive / False Negative Interpretation

False positives are legitimate transactions sent to review. Their cost is analyst time, potential customer friction, and delayed approval. False negatives are fraud transactions left outside the selected review queue. Their cost is expected fraud loss and regulatory exposure. The selected policy intentionally accepts some false positives to materially reduce high-value false negatives.

## Next Decision

Before production deployment, the bank should calibrate the threshold with real cost inputs:

- Average fraud loss after recoveries
- Review team hourly cost and daily capacity
- Customer friction penalty for delayed approvals
- Required fraud capture target by product and channel
