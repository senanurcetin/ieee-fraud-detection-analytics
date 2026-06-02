# Fraud Analytics Web Report

This web application is the public presentation layer for the fraud analytics project. It recreates a professional BI-style fraud report as a modern browser dashboard, using FastAPI plus a static HTML/CSS/JavaScript frontend connected to the governed reporting marts.

The application is analytical by design. It is not an operations workflow, ticketing tool, or monitoring console.

## Report Pages

1. **Executive Fraud Overview**
   - Portfolio KPIs, exposure, trend, product risk, segment contribution, and executive takeaways.

2. **Fraud Trend Analysis**
   - Relative-day fraud movement, transaction volume context, hourly patterns, and drift interpretation.

3. **Transaction Amount Analysis**
   - Amount-band risk, product x amount heatmaps, amount-score scatter, and amount distribution comparison.

4. **Customer Risk Analysis**
   - Masked customer proxies using identity status, email group, device type, and product context.

5. **Geographic Fraud Analysis**
   - Geography readiness page. IEEE-CIS does not contain native country, city, or IP-location fields, so maps are disabled until enrichment exists.

6. **Behavioral Pattern Analysis**
   - Relative-hour, payment, email, device, score, and amount behavior patterns.

7. **Feature Importance Analysis**
   - Feature importance, feature family contribution, missingness versus importance, and masked-feature interpretation.

8. **Model Performance Analysis**
   - ROC-AUC, PR-AUC, precision, recall, top-decile lift, risk band distribution, confusion matrix, and threshold simulation.

9. **Key Insights & Recommendations**
   - Recommendation matrix, expected exposure reduction, analyst summary, and business action register.

## Interaction Model

- Sidebar page navigation.
- Central metric layer for fraud rate, exposure, capturable exposure, missed exposure, precision, recall, workload, and net benefit.
- Global slicers for relative day window, product, amount band, email group, identity status, and risk band.
- Chart click cross-filtering for product, amount, email, identity, and risk-band visuals.
- BI-style segment drill-through drawer with fraud rate, lift, fraud share, exposure proxy, priority, and same-family nested drilldown.
- Hover tooltips for chart values.
- Drill-through tables for segment and transaction-level analytical samples.
- Threshold dropdown and scrubber that recalculate capture, precision, review workload, and missed exposure.
- Export current report page to PDF through browser print.
- Export filtered data to CSV.
- Dark and light mode toggle.

## Data Contract

The frontend reads:

- `/api/dashboard`
- `/api/metadata`
- `/api/enterprise/cases?limit=240` for a transaction-level analytical sample used in scatter plots and drill-through tables.

Core reporting groups:

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
- `rpt_threshold_simulation`
- `fact_train_transactions` for governed niche drilldowns

## Analytical Guardrails

- `TransactionDT` is relative elapsed time, not a calendar timestamp.
- Geography is not visualized as a map until external enrichment exists.
- Customer risk uses masked proxies, not real customer profile attributes.
- Masked Vesta features are presented as statistical signals, not confirmed business definitions.
- Model output is presented as analytical prioritization and threshold simulation, not autonomous decisioning.

## Local Run

For BigQuery:

```powershell
$env:GCP_PROJECT_ID="your-gcp-project"
$env:BQ_DATASET="fraud_project_reporting"
$env:BIGQUERY_LOCATION="US"
$env:GOOGLE_APPLICATION_CREDENTIALS="<private-service-account-json-path>"

uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
```

For local DuckDB QA:

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
npx vercel deploy --prod --yes
```

Required environment variables:

- `GCP_PROJECT_ID`
- `BQ_DATASET`
- `BIGQUERY_LOCATION`
- `BIGQUERY_MAX_BYTES_BILLED`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON_B64`

Never commit credential files to the repository.
