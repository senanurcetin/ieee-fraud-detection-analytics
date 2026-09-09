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

IEEE-CIS contains exactly one monetary column, `TransactionAmt`. There is no
review cost, no chargeback cost, no recovery rate and no margin. Every currency
figure beyond fraud-labelled amount is therefore an assumption, and the
dashboard states both of its assumptions on screen rather than embedding them.

Measured from the dataset:

- Fraud-labelled amount, filterable by score threshold and segment.
- Flagged volume and precision at each validation threshold.

Assumed, and adjustable in the threshold simulator:

| Parameter | Default | Basis |
|---|---:|---|
| Cost per reviewed false positive | $5.00 | Automation-assisted screening sits near $3-5 per case; full manual investigations at mid-size institutions run $25-50. |
| Loss per $1 of fraud | 1.0 | Conservative: counts only the transaction amount. LexisNexis' 2025 True Cost of Fraud study puts the fully loaded figure nearer 4.6-5.0 once operations, chargeback handling and customer churn are included. |

The net benefit calculation is:

```
net benefit = (captured fraud amount x loss rate) - (false positives x review cost)
```

Both sides are priced at the same loss rate. Catching fraud avoids a loss
rather than earning revenue, so crediting captured fraud at face value while
charging missed fraud at a fraction would make the two halves of the comparison
incommensurable. Missed fraud is not penalised a second time: it is already
absent from the avoided-loss term.

This is a decision frame, not realised savings. Move the loss rate to 4.6 and
the recommended operating point shifts toward higher capture; raise the review
cost and it shifts toward a narrower queue. Showing that sensitivity is the
point.

## Sensitivity Scenarios

Set these directly in the dashboard's threshold simulator.

| Scenario | Review cost | Loss per fraud dollar | What it tests |
|---|---:|---:|---|
| Conservative | $5 | 1.0 | Only the transaction amount is at risk. Floor case. |
| Higher review cost | $25 | 1.0 | Full manual investigation instead of assisted screening. |
| Fully loaded loss | $5 | 4.6 | LexisNexis merchant multiplier, including downstream operational and trust costs. |
| Stress case | $25 | 4.6 | Expensive reviews against fully loaded fraud cost; defines the decision boundary before a production pilot. |

These are scenario controls, not accounting claims.

## False Positive / False Negative Interpretation

False positives are legitimate transactions flagged by the selected threshold. Their cost is analyst time, potential customer friction, and delayed approval. False negatives are fraud transactions left outside the selected threshold. Their cost is expected fraud loss and regulatory exposure. The selected policy intentionally accepts some false positives to materially reduce high-value false negatives.

## Next Decision

Before production deployment, the bank should calibrate the threshold with real cost inputs:

- Average fraud loss after recoveries
- Review team hourly cost and daily capacity
- Customer friction penalty for delayed approvals
- Required fraud capture target by product and channel

