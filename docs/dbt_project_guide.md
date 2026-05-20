# dbt Project Guide

## Layers

The dbt project follows a layered analytics model:

1. `sources.yml`: raw Kaggle tables and model support outputs.
2. `models/staging`: type normalization and field naming.
3. `models/intermediate`: joins and feature engineering.
4. `models/marts`: reusable analytical marts.
5. `models/powerbi`: DirectQuery-friendly reporting tables.

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
- Power BI contract tests
- Business-rule tests for watchlist and review strategy tables

Run:

```bash
dbt build --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target dev
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

## Empty dbt Directories

The `analyses`, `seeds`, and `snapshots` directories are intentionally kept with `.gitkeep` files. They provide standard dbt project structure for future ad-hoc analysis, reference seed tables, and slowly changing dimension snapshots.

## Packages

`packages.yml` is intentionally empty. The current implementation uses local macros instead of external package dependencies to keep the build surface small and explicit. External packages can be added later if a new test or utility cannot be implemented cleanly in local macros.

## Exposures

The Power BI report is declared as the `fraud_project_v2` exposure in `models/powerbi/_powerbi.yml`.
