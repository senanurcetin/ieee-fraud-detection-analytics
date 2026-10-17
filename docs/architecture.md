# Architecture

This project is structured as an analytics engineering pipeline, not as a notebook-only analysis. The goal is to move from raw competition data to tested analytical marts, model-driven risk scores, and an executive reporting layer.

## End-to-End Flow

```mermaid
flowchart LR
    A["Kaggle IEEE-CIS CSV files"] --> B["DuckDB local raw store"]
    B --> C["Python feature profiling and ML scoring"]
    B --> D["BigQuery fraud_project_raw"]
    D --> E["dbt staging"]
    E --> F["dbt intermediate"]
    F --> G["dbt marts"]
    C --> G
    G --> H["dbt reporting layer"]
    H --> S["Verified historical JSON snapshot"]
    S --> I["FastAPI analytics API"]
    I --> J["Nine-page NEXUS dashboard"]
```

## BigQuery Datasets

| Dataset | Purpose |
|---|---|
| `fraud_project_raw` | Raw Kaggle tables and model support outputs |
| `fraud_project_staging` | Typed and normalized source views |
| `fraud_project_intermediate` | Joined transaction and identity records with engineered features |
| `fraud_project_mart` | Reconciled fraud, segment, risk-band, time, amount, and quality marts |
| `fraud_project_reporting` | Historical reporting tables used to generate a versioned web dashboard snapshot |

## dbt Model Layers

| Layer | Main models | Responsibility |
|---|---|---|
| Staging | `stg_transactions`, `stg_identity` | Type casting, safe naming, TransactionDT-derived fields, amount-cent features |
| Intermediate | `int_fraud_joined`, `int_features` | Transaction and identity join, product/payment/email/device segmentation |
| Marts | `mart_*` | Fraud summary, risk bands, amount bands, daily drift, payment/email risk, quality checks |
| Reporting | `fact_train_transactions`, `rpt_*` | Executive KPIs, web visual tables, segment watchlists, model performance, quality contracts |

## Reporting Design

The published dashboard normally serves **committed historical JSON snapshots** through FastAPI. The snapshots are derived from the `fraud_project_reporting` layer but are not live BigQuery query results. Internal source refresh or independent data verification is a separate authenticated workflow. Raw Kaggle tables and staging models are intentionally excluded from the public presentation surface. Source freshness and model-scoring limitations are disclosed in the UI and [release status](RELEASE_STATUS.md).

## Quality Gates

- Source row-count tests verify Kaggle table completeness.
- Staging tests validate key fields, ranges, and transaction uniqueness.
- Reconciliation tests check fact and mart consistency.
- Risk-band tests enforce expected risk labels and monotonic behavior.
- Report-readiness tests verify that the web reporting layer is complete.

Historical BigQuery/dbt build verification (not an assertion about the current source or latest deployment):

```text
dbt build: PASS=164 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=165
Scope: 38 models, 126 data tests, 10 sources, 1 exposure
```
