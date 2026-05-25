# 03 - Analysis Hypotheses

## H1 - Product Family Separates Risk

Hypothesis: product categories do not carry the same fraud rate.

Result: Product C has an 11.69% fraud rate, roughly 3.34x the portfolio baseline. Product family is one of the clearest executive-level segmentation dimensions.

## H2 - Identity Coverage Is a Risk Signal

Hypothesis: transactions with identity records have a different risk profile from transactions without identity records.

Result: identity-present transactions show a 7.85% fraud rate, compared with 2.09% for identity-missing transactions. Identity coverage is not only a data completeness measure; it is a behavioral segmentation signal.

## H3 - Amount Risk Is Nonlinear

Hypothesis: fraud rate does not increase monotonically with transaction amount.

Result: very low-value transactions and higher-value bands show elevated risk compared with mid-range amounts. A single amount threshold would miss this shape.

## H4 - Email Domains Create Operational Segments

Hypothesis: purchaser email-domain groups separate fraud risk and review volume.

Result: high-volume mainstream domains and selected higher-risk groups require different monitoring logic. Email domain should be used with product, amount, and model score, not as a standalone decision rule.

## H5 - Relative Time Windows Matter

Hypothesis: fraud concentration changes across relative day and hour windows.

Result: the project derives relative day and relative hour from `TransactionDT` and monitors drift through rolling fraud-rate metrics. These patterns support staffing and threshold discussions, but they are not real calendar dates.

## H6 - Model Risk Bands Enable Review Prioritization

Hypothesis: model scores can create a manageable review queue without becoming an automated decline engine.

Result: the High + Critical queue reviews about 5.06% of validation transactions while capturing 59.4% of fraud labels at 40.4% precision. This is the recommended starting operating point.

## Presentation Frame

The analysis should start with fraud concentration, not tooling. The recommended story sequence is:

1. Baseline fraud is low, so averages hide risk.
2. Product and identity reveal the first concentration layer.
3. Amount, payment, email, and relative time explain operational patterns.
4. Model risk bands convert the evidence into review queues.
5. dbt tests, row-count reconciliation, and data quality checks prove the pipeline is trustworthy.
