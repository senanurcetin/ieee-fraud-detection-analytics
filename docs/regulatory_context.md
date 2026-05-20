# Regulatory Context

## Positioning

This project is framed as fraud monitoring and review prioritization, not as an automated adverse decisioning system. The model ranks transactions for analyst attention; final action should remain governed by policy, auditability, and human approval.

## PSD2 and Strong Customer Authentication

For card-not-present and digital payment scenarios, PSD2-style strong customer authentication principles are relevant to the risk narrative:

- High-risk segments can trigger stronger authentication or step-up review.
- Low-risk segments can remain on a standard monitoring path to reduce friction.
- Risk scoring should be explainable enough to support exemption and step-up decisions.

The report's risk bands support this logic by separating `Critical`, `High`, `Elevated`, and `Low` review priorities.

## AML and Financial Crime Monitoring

Fraud analytics overlaps with broader financial crime monitoring but should not be treated as a complete AML solution. The relevant controls are:

- Segment-level monitoring for unusual concentration.
- Watchlist-style outputs for product, device, payment, and email groups.
- Audit trails for model version, threshold, and review policy.
- Escalation rules for high-risk queues.

## GDPR and Data Minimization

The IEEE-CIS dataset is anonymized, and this project does not redistribute raw data. In a production banking environment, the equivalent controls would be:

- Process only fields needed for fraud prevention.
- Avoid exposing direct personal identifiers in dashboards.
- Restrict analyst access by role.
- Keep model explanations at feature-family or segment level when individual-level detail is not required.
- Retain model outputs and review decisions according to the institution's retention policy.

## Governance Requirements Before Production

Before moving from portfolio analytics to a production banking workflow, the following governance controls should be added:

- Model approval record with validation metrics and known limitations.
- Threshold approval and change log.
- Periodic bias and segment stability review.
- Monitoring for score drift and fraud-rate drift.
- Incident process for abnormal fraud spikes or degraded model performance.
