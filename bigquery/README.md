# BigQuery Deployment

This project deploys the fraud analytics pipeline into a layered BigQuery architecture under the `fraud_project` naming convention. The deployment flow loads raw Kaggle files, runs dbt transformations, executes quality tests, and publishes DirectQuery-friendly Power BI tables.

## Dataset Layout

| Dataset | Purpose |
|---|---|
| `fraud_project_raw` | Raw Kaggle CSV tables and ML support outputs |
| `fraud_project_staging` | Typed staging views |
| `fraud_project_intermediate` | Joined and feature-engineered transaction layer |
| `fraud_project_mart` | Business-ready fraud analytics marts |
| `fraud_project_powerbi` | Power BI DirectQuery reporting layer |

## Required Environment Variables

Set credentials through environment variables. Do not pass local machine paths or commit service-account JSON files.

```powershell
$env:GCP_PROJECT_ID = "your-gcp-project"
$env:BIGQUERY_LOCATION = "US"
$env:GOOGLE_APPLICATION_CREDENTIALS = "/secure/path/service-account.json"
```

## Deployment Command

```powershell
.\scripts\deploy_bigquery.ps1 `
  -Credentials $env:GOOGLE_APPLICATION_CREDENTIALS `
  -ProjectId $env:GCP_PROJECT_ID `
  -Location $env:BIGQUERY_LOCATION `
  -ReportingDataset "fraud_project_powerbi"
```

## dbt Production Commands

```powershell
dbt run --project-dir . --profiles-dir config\dbt --profile ieee_fraud_detection --target prod
dbt test --project-dir . --profiles-dir config\dbt --profile ieee_fraud_detection --target prod
```

For a single command quality gate:

```powershell
dbt build --project-dir . --profiles-dir config\dbt --profile ieee_fraud_detection --target prod
```

Latest verified production build:

```text
PASS=123 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=124
```

## Power BI Reporting Tables

The `fraud_project_powerbi` dataset should expose these reporting tables:

- `fact_train_transactions`
- `pbi_executive_kpis`
- `pbi_product_risk`
- `pbi_identity_risk`
- `pbi_identity_product_coverage`
- `pbi_amount_bands`
- `pbi_time_amount_signals`
- `pbi_daily_drift`
- `pbi_payment_heatmap`
- `pbi_email_domain_risk`
- `pbi_model_risk_bands`
- `pbi_threshold_simulation`
- `pbi_review_strategy`
- `pbi_segment_watchlist`
- `pbi_feature_importance`
- `pbi_data_quality_scorecard`
- `pbi_quality_contract`
- `pbi_report_readiness`
- `pbi_report_narrative`

## Minimum IAM Roles

The service account needs:

- BigQuery Job User
- BigQuery Data Editor
- BigQuery Data Viewer

## Operational Notes

- Raw transaction tables are wide and should not be used directly in Power BI.
- Power BI should connect to `fraud_project_powerbi` only.
- `config/dbt/profiles.yml` is a sanitized profile template that reads credentials from environment variables.
- Service-account JSON files are excluded from Git and must remain outside the repository.
