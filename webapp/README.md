# Fraud Risk Intelligence Platform

This web application is the only public presentation layer for the fraud analytics project. It turns the dbt-built BigQuery reporting layer into an English-first enterprise fraud intelligence platform for executives, fraud analysts, risk teams, and model monitoring stakeholders.

The interface is intentionally web-only and does not depend on any paid visualization service.

## Product Scope

The platform answers four operational questions:

- What happened: fraud volume, loss exposure, and drift movement.
- Why it happened: segment concentration, model drivers, and masked entity context.
- How serious it is: review workload, capture potential, precision, and alert severity.
- What to do next: analyst queue priority, case action, threshold policy, and monitoring response.

## Enterprise Pages

1. **Executive Command Center**
   - Focused KPI strip: total transactions, fraud rate, loss exposure, capturable exposure, high-risk workload, and precision/recall.
   - Large visuals for fraud trend, loss trend, segment contribution, Pareto concentration, and risk score distribution.

2. **Analyst Investigation Queue**
   - Case queue grouped by Critical, High Risk, Medium Risk, and Low Risk.
   - Columns include transaction ID, risk score, category, amount, product, device, email group, identity status, prior-fraud proxy, model confidence, recommended action, and SLA priority.

3. **Transaction Detail**
   - Case workspace for one transaction.
   - Includes risk score, transaction summary, top risk factors, feature contribution cards, recommended analyst action, and an audit-trail placeholder.

4. **Fraud Intelligence Center**
   - Hierarchical segment drilldowns instead of unrelated segment comparisons.
   - Supported paths include Product -> Amount band, Amount band -> Product, Payment -> Email group, Email group -> Product, and Identity -> Product.
   - Includes contribution waterfall, segment Pareto, heatmaps, relative-time signals, and masked entity relationship context.

5. **Model Monitoring**
   - Model KPIs: ROC-AUC, PR-AUC, precision, recall, false positive rate, and top-decile lift.
   - Threshold simulator for analyst capacity, review cost, missed-fraud loss, workload, capture, precision, and estimated exposure.
   - Feature importance, risk distribution, prediction distribution, and drift proxy visuals.

6. **Alert Management**
   - Historical replay alert simulation from IEEE-CIS relative time.
   - Covers fraud drift, critical queue pressure, missingness spikes, segment concentration, and model-confidence indicators.

Data Trust is embedded as a drawer and appendix rather than a main presentation page. It shows readiness, data source, table count, model metadata, methodology limits, and compliance notes.

## Data Contract

The platform keeps `/api/dashboard` backward compatible and adds enterprise endpoints:

- `/api/enterprise/summary`
- `/api/enterprise/cases`
- `/api/enterprise/cases/{transaction_id}`
- `/api/enterprise/segments`
- `/api/enterprise/alerts`
- `/api/enterprise/model-monitoring`
- `/api/enterprise/metadata`

Core reporting tables:

- `rpt_executive_kpis`
- `rpt_segment_watchlist`
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
- `rpt_review_strategy`
- `rpt_threshold_simulation`
- `rpt_quality_contract`
- `rpt_report_readiness`
- `fact_train_transactions`

The application does not show country, user age, or real customer network fields because IEEE-CIS does not provide those attributes. Masked entity relationships are shown only as anonymized analytical proxies.

## Local Run

For BigQuery:

```powershell
$env:GCP_PROJECT_ID="your-gcp-project"
$env:BQ_DATASET="fraud_project_reporting"
$env:BIGQUERY_LOCATION="US"
$env:GOOGLE_APPLICATION_CREDENTIALS="<private-service-account-json-path>"

uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

For zero-cost local QA from the DuckDB development build:

```powershell
$env:WEB_DATA_BACKEND="duckdb"
$env:FRAUD_PROJECT_DUCKDB_PATH="data/processed/ieee_fraud.duckdb"
$env:WEB_CACHE_SECONDS="30"

uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

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
- `Print / Save PDF` uses browser print styles.
- `Copy executive summary` creates a short presentation-ready narrative from the live data.

## Cost and Quota Guardrails

- API responses are cached in memory.
- `WEB_CACHE_SECONDS` controls cache duration.
- `BIGQUERY_MAX_BYTES_BILLED` limits query size.
- Expensive interactions are served from pre-aggregated reporting marts or constrained reporting fact queries.
