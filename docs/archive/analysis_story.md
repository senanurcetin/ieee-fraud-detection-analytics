# Analysis Story

## Core Question

Where does fraud concentrate, and which threshold and segment policies should management prioritize?

## Executive Narrative

1. Fraud is rare but concentrated: the portfolio baseline is 3.50%.
2. Product risk is uneven: Product C is materially above the baseline, while Product W is lower risk at portfolio level.
3. Identity availability is a signal: identity-present transactions show higher fraud concentration than identity-missing transactions.
4. Amount risk is nonlinear: very low-value and higher-value bands both need monitoring.
5. Payment and email attributes add explainable BI segments.
6. Model scores should be used as threshold-policy evidence, not as a fully automated decision engine.

## Recommended Presentation Flow

Open with the class imbalance problem, then prove that fraud is not randomly distributed. Move through product, identity, amount, payment, email, and relative time signals. Close with model risk bands, threshold simulation, and data trust evidence.

The architecture should support the story, not replace it. Use dbt, BigQuery, and test evidence after the business insights are clear.
