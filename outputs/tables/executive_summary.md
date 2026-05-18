# IEEE-CIS Fraud Detection Executive Summary

## Core Metrics

- Total transactions: 590,540
- Fraud transactions: 20,663
- Fraud rate: 3.50%
- Identity coverage: 24.42%
- Median transaction amount: $68.77
- P95 transaction amount: $445.00
- Validation AUC: 0.917
- Validation average precision: 0.531

## Board-Level Takeaway

The dataset is a rare-event fraud problem with strong engineered feature signal, structural missingness, and meaningful risk concentration by product, identity coverage, transaction amount, and model-derived risk band. The recommended analytics operating model is raw landing in BigQuery free tier, dbt Core transformations, Python/LightGBM scoring, and Power BI consumption from curated marts.
