# Operational Playbook

## Purpose

The model output is converted into an analyst review queue. The operating rule is intentionally simple: prioritize scarce review capacity where fraud concentration and model confidence are highest.

## Review Queue Policy

| Risk band | Queue priority | Expected action | SLA |
|---|---|---|---|
| Critical | Immediate review | Manual investigation before approval or escalation to step-up authentication | Same session or same day |
| High | Priority review | Same-day investigation, rule-set check, and segment monitoring | Same day |
| Elevated | Queue monitoring | Sample-based review and weekly trend monitoring | Weekly |
| Low | Standard monitoring | No manual action unless another control triggers | Standard process |

## Analyst Workflow

1. Start with the `Critical` queue and validate transaction context, product code, amount band, card attributes, email group, and identity coverage.
2. Move to the `High` queue until daily review capacity is exhausted.
3. For each reviewed transaction, record decision outcome, reason code, and whether additional authentication was requested.
4. Review `Elevated` segments weekly to detect emerging patterns that are not yet large enough for full manual review.
5. Feed confirmed outcomes back into the next model training cycle.

## Escalation Rules

Escalate to fraud operations management when one of the following occurs:

- Daily fraud rate exceeds the seven-day moving baseline.
- Product C or a high-risk payment segment grows materially in transaction share.
- High + Critical review queue exceeds available analyst capacity.
- Precision in reviewed queues drops below the approved threshold.
- A new email or device segment enters the top risk watchlist.

## Controls

Operational controls should include:

- Approved threshold table.
- Reviewer decision audit trail.
- Weekly segment watchlist.
- Monthly model performance review.
- Data-quality scorecard for missingness and source row reconciliation.

## Production Extension

For real-time use, the batch scoring layer can be extended into an online scoring service:

- Transaction event arrives from payment authorization flow.
- Feature service retrieves recent card, identity, amount, and device attributes.
- Model service returns score and risk band.
- Decision service applies policy: approve, step-up authentication, manual review, or decline under approved rules.
- Outcomes are written back for monitoring and retraining.
