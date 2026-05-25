# dbt Project Guide

## Layers

The dbt project follows a layered analytics model:

1. `sources.yml`: raw Kaggle tables and model support outputs.
2. `models/staging`: type normalization and field naming.
3. `models/intermediate`: joins and feature engineering.
4. `models/marts`: reusable analytical marts.
5. `models/reporting`: presentation-ready reporting tables for the live web dashboard.

## Source Tables

The `raw` source includes:

- `train_transaction`
- `train_identity`
- `test_transaction`
- `test_identity`
- `sample_submission`
- `ml_predictions`
- `feature_missingness`
- `feature_importance`

Row-count tests validate the expected Kaggle table sizes.

## Tests

The project includes:

- Source row-count tests
- Not-null and uniqueness tests
- Accepted value tests
- Custom range tests
- Reconciliation tests
- Risk band completeness tests
- Reporting layer contract tests
- Business-rule tests for watchlist and review strategy tables
- Relative TransactionDT and amount-cent validation tests
- Product-level identity coverage tests

Run:

```bash
dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev
```

## Macros

`macros/generic_tests.sql` defines custom generic tests:

- `accepted_range`
- `not_negative`
- `row_count_equals`
- `row_count_between`
- `fraud_rate_between`

`macros/sql_helpers.sql` contains warehouse-compatible SQL helpers.

`macros/generate_schema_name.sql` maps dbt model folders to the intended BigQuery dataset names.

## IEEE-CIS Specific Enhancements

The project includes dataset-specific models for common IEEE-CIS pitfalls:

- `transaction_hour` and `relative_day_of_week` are derived from elapsed `TransactionDT` seconds, not from a real timestamp.
- `synthetic_uid_card_addr` is created from `card1 + addr1` for segment-level analysis only.
- `transaction_amount_cents` and `is_round_amount` expose amount-decimal behavior.
- `purchaser_email_risk_group` groups raw domains into business-facing buckets.
- `mart_identity_product_coverage` shows identity coverage and fraud rate by ProductCD.
- `mart_time_amount_signals` shows relative-hour and amount-decimal fraud signals.

## Empty dbt Directories

The `analyses`, `seeds`, and `snapshots` directories are intentionally kept with `.gitkeep` files. They provide standard dbt project structure for future ad-hoc analysis, reference seed tables, and slowly changing dimension snapshots.

## Packages

`packages.yml` is intentionally empty. The current implementation uses local macros instead of external package dependencies to keep the build surface small and explicit. External packages can be added later if a new test or utility cannot be implemented cleanly in local macros.

## Exposures

The executive web dashboard is declared as the `fraud_project_v2` reporting exposure in `models/reporting/_reporting.yml`. The folder name is retained for backward compatibility with the original reporting dataset name.
