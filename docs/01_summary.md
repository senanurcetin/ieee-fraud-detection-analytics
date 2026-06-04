# 01 - Executive Summary

## Objective

`fraud_project` is an end-to-end fraud analytics project built for executive risk review. It turns the IEEE-CIS transaction and identity files into governed warehouse tables, dbt reporting marts, LightGBM risk scores, and a live web dashboard.

The core business question is:

> Where does fraud concentrate, and which threshold and segment policies should management prioritize?

## Dataset Scope

- Profiled train transactions: 590,540
- Fraud-labeled transactions: 20,663
- Baseline fraud rate: 3.50%
- Transactions with identity records: 144,233
- Identity coverage rate: 24.42%
- Product categories: 5
- Feature columns in the original dataset: 431

`TransactionDT` is treated as elapsed seconds from a reference point, not as a real timestamp. Relative day and hour fields are derived for trend and operational pattern analysis.

## Key Findings

1. Fraud is rare at portfolio level, but it is highly concentrated in specific product, identity, payment, email, amount, and model-score segments.
2. Product C shows an 11.69% fraud rate, roughly 3.34x the portfolio baseline.
3. Identity-present transactions have a 7.85% fraud rate, while identity-missing transactions show 2.09%.
4. Amount risk is not linear: very low values and higher-value bands both require monitoring.
5. Email and payment attributes add explainable operational segmentation when combined with product and model risk bands.
6. The top 5% validation score band captures 58.32% of fraud labels at 40.13% precision; the fixed 0.50 threshold raises capture to 69.78% with higher workload.

## Management Message

The project does not present the model as an automated decline engine. It positions machine learning as threshold-policy evidence that concentrates low-prevalence fraud into measurable risk bands. Business rules and segment analytics remain visible so that analysts can explain why a segment or threshold should be prioritized.

## Deliverables

- BigQuery dataset architecture for raw, staging, intermediate, mart, and reporting layers.
- dbt models and tests for repeatable transformation and reconciliation.
- LightGBM scoring pipeline with time-based validation and explainability artifacts.
- FastAPI web API connected to the BigQuery reporting layer.
- English-first executive web dashboard deployed on Vercel.
- Documentation covering methodology, business impact, security, and analytical policy guidance.

