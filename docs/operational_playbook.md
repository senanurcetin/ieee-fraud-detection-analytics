# Analytical Policy Playbook

## Purpose

The model output is converted into threshold-policy scenarios for the BI dashboard. The rule is intentionally simple: prioritize scarce business attention where fraud concentration and model confidence are highest.

## Threshold Policy

| Risk band | Policy priority | Expected action | Cadence |
|---|---|---|---|
| Critical | Critical focus | Additional verification, policy calibration, and segment review | Same day |
| High | High-priority band | Rule-set check and segment monitoring | Daily |
| Elevated | Control sample | Sample-based control check and trend monitoring | Weekly |
| Low | Baseline | No special action unless another control triggers | Standard process |

## Analyst Review Frame

1. Start with Critical and High score bands and validate product code, amount band, card attributes, email group, and identity coverage.
2. Compare focused top-score validation evidence with the fixed 0.50 threshold scenario.
3. Record business assumptions: false-positive review cost, false-negative loss, and available capacity.
4. Review Elevated segments weekly to detect emerging patterns that are not yet large enough for policy escalation.
5. Feed confirmed outcomes back into the next model training cycle.

## Escalation Rules

Escalate to risk management when one of the following occurs:

- Daily fraud rate exceeds the seven-day moving baseline.
- Product C or a high-risk payment segment grows materially in transaction share.
- Selected threshold flagged volume exceeds available capacity.
- Precision in the selected threshold band drops below the approved threshold.
- A new email or device segment enters the top risk watchlist.

## Controls

Operational controls should include:

- Approved threshold table.
- Decision audit trail.
- Weekly segment watchlist.
- Monthly model performance review.
- Data-quality scorecard for missingness and source row reconciliation.

## Production Extension

For real-time use, the batch scoring layer can be extended into an online scoring service:

- Transaction event arrives from a payment authorization flow.
- Feature service retrieves recent card, identity, amount, and device attributes.
- Model service returns score and risk band.
- Decision service applies approved policy: approve, step-up authentication, business review, or decline under approved rules.
- Outcomes are written back for monitoring and retraining.
