# Fraud Risk Intelligence Web Dashboard

This web application is the only public presentation layer for the fraud analytics project. It serves an English-first executive dashboard from a FastAPI backend and reads only the dbt-built BigQuery reporting tables in `fraud_project_reporting`.

## What It Shows

- Executive KPI strip for transaction volume, fraud volume, fraud rate, identity coverage, review workload, and fraud capture.
- Segment comparison between two risk cuts with fraud rate, lift, fraud share, transaction share, average amount, and priority.
- Drill-through drawer with workload impact, recommended action, and copy-ready presentation insight.
- Fraud contribution waterfall and Pareto concentration view from `rpt_segment_watchlist`.
- Model operations simulator with analyst capacity, false-positive review cost, and false-negative loss assumptions.
- Alert simulation for fraud drift, critical queue pressure, missingness, and readiness status.
- Data trust page with row-count contract, readiness gate, missingness scorecard, and live lineage.
- KPI dictionary, methodology limitations, and analyst action register for executive-ready interpretation.

## Data Contract

The API reads these 18 reporting tables:

- `rpt_executive_kpis`
- `rpt_product_risk`
- `rpt_identity_risk`
- `rpt_identity_product_coverage`
- `rpt_amount_bands`
- `rpt_daily_drift`
- `rpt_time_amount_signals`
- `rpt_payment_heatmap`
- `rpt_email_domain_risk`
- `rpt_model_risk_bands`
- `rpt_feature_importance`
- `rpt_data_quality_scorecard`
- `rpt_segment_watchlist`
- `rpt_review_strategy`
- `rpt_threshold_simulation`
- `rpt_report_narrative`
- `rpt_quality_contract`
- `rpt_report_readiness`

No raw transaction table is queried by the dashboard. All visible analytics come from pre-aggregated reporting marts or client-side calculations over the API payload.

The API also exposes `/api/metadata`, which publishes:

- KPI definitions used by the dashboard.
- Dataset methodology notes and analytical limitations.
- Operating assumptions for capacity, review cost, missed-loss exposure, and API caching.
- Release quality gates and data contract metadata.

## Local Run

```powershell
$env:GCP_PROJECT_ID="your-gcp-project"
$env:BQ_DATASET="fraud_project_reporting"
$env:BIGQUERY_LOCATION="US"
$env:GOOGLE_APPLICATION_CREDENTIALS="<private-service-account-json-path>"

uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

For zero-cost local QA after `dbt build --target dev`, the API can read the local DuckDB reporting schema instead of BigQuery:

```powershell
$env:WEB_DATA_BACKEND="duckdb"
$env:FRAUD_PROJECT_DUCKDB_PATH="data/processed/ieee_fraud.duckdb"

uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Production keeps the default `bigquery` backend.

## Vercel Runtime

Deploy the `webapp` folder as the Vercel project root:

```powershell
cd webapp
npx vercel link --yes --project fraud-project-web
npx vercel deploy --prod --yes
```

Vercel cannot read local credential files. Configure these environment variables in the Vercel project:

- `GCP_PROJECT_ID`
- `BQ_DATASET`
- `BIGQUERY_LOCATION`
- `BIGQUERY_MAX_BYTES_BILLED`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON_B64`

`GOOGLE_APPLICATION_CREDENTIALS_JSON_B64` must contain the base64-encoded service-account JSON content. Never commit credential files to the repository.

## Export Options

- `Export JSON` downloads the current API payload for audit or offline review.
- `Print / Save PDF` uses browser print styles for the active dashboard tab.
- `Copy executive summary` creates a short presentation-ready narrative from the current live data.

## Cost and Quota Guardrails

- API responses are cached in memory for 10 minutes by default.
- Set `WEB_CACHE_SECONDS` to tune cache duration.
- Set `BIGQUERY_MAX_BYTES_BILLED` to enforce a query cost limit.
- The dashboard reads only small `rpt_*` reporting tables, which keeps BigQuery usage within free-tier-friendly limits for portfolio traffic.
