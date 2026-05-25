# Live Web Dashboard

This web application is an alternative presentation layer for the same BigQuery reporting tables used by the Power BI report. It serves a Turkish executive dashboard from a FastAPI backend and reads only the dbt-built `fraud_project_powerbi` tables.

## Data Contract

The API reads these reporting tables:

- `pbi_executive_kpis`
- `pbi_product_risk`
- `pbi_amount_bands`
- `pbi_daily_drift`
- `pbi_payment_heatmap`
- `pbi_email_domain_risk`
- `pbi_model_risk_bands`
- `pbi_feature_importance`
- `pbi_data_quality_scorecard`
- `pbi_segment_watchlist`
- `pbi_review_strategy`
- `pbi_threshold_simulation`
- `pbi_report_readiness`

## Local Run

```powershell
$env:GCP_PROJECT_ID="your-gcp-project"
$env:BQ_DATASET="fraud_project_powerbi"
$env:BIGQUERY_LOCATION="US"
$env:GOOGLE_APPLICATION_CREDENTIALS="<private-service-account-json-path>"

uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

## Notes

- The dashboard queries pre-aggregated `pbi_*` tables, not the raw transaction table.
- API responses are cached in memory for 10 minutes by default.
- Set `WEB_CACHE_SECONDS` to change the cache duration.
- Set `BIGQUERY_MAX_BYTES_BILLED` to enforce a query cost guardrail.

## Vercel Runtime

Deploy this folder as the Vercel project root:

```powershell
cd webapp
npx vercel link --yes --project fraud-project-web
npx vercel deploy --prod --yes
```

Vercel does not have access to local credential files. Configure these environment variables in the Vercel project:

- `GCP_PROJECT_ID`
- `BQ_DATASET`
- `BIGQUERY_LOCATION`
- `BIGQUERY_MAX_BYTES_BILLED`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON_B64`

`GOOGLE_APPLICATION_CREDENTIALS_JSON_B64` must contain the base64-encoded service-account JSON content. Do not commit credential files to the repository.
