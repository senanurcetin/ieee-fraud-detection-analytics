param(
    [Parameter(Mandatory = $true)]
    [string]$Credentials,

    [string]$ProjectId = "workintech-working",
    [string]$Location = "US",
    [string]$ReportingDataset = "fraud_project_powerbi"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Credentials)) {
    throw "Credential file not found: $Credentials"
}

$env:GCP_PROJECT_ID = $ProjectId
$env:BIGQUERY_LOCATION = $Location
$env:BIGQUERY_REPORTING_DATASET = $ReportingDataset
$env:GOOGLE_APPLICATION_CREDENTIALS = (Resolve-Path -LiteralPath $Credentials).Path

$python = "python"
$dbt = Join-Path $env:APPDATA "Python\Python312\Scripts\dbt.exe"
if (-not (Test-Path -LiteralPath $dbt)) {
    $dbt = "dbt"
}

& $python src\prepare_raw_and_ml.py
& $python src\upload_to_bigquery.py --project-id $ProjectId --location $Location --credentials $env:GOOGLE_APPLICATION_CREDENTIALS
& $dbt build --project-dir . --profiles-dir config\dbt --profile ieee_fraud_detection --target prod
& $python src\export_powerbi_and_charts.py
& $python src\create_powerbi_template.py
& $python src\create_powerbi_connection_files.py
& $python src\build_fraud_project_v2_pbix.py

Write-Host ""
Write-Host "BigQuery deployment complete."
Write-Host "Power BI reporting dataset: $ProjectId.$ReportingDataset"
Write-Host "Recommended tables:"
Write-Host "  - fact_train_transactions"
Write-Host "  - mart_model_predictions"
Write-Host "  - mart_fraud_summary"
Write-Host "  - mart_daily_stats"
Write-Host "  - mart_amount_bands"
Write-Host "  - mart_product_device_stats"
Write-Host "  - mart_email_domain_stats"
Write-Host "  - mart_risk_band_stats"
Write-Host "  - pbi_executive_kpis"
Write-Host "  - pbi_product_risk"
Write-Host "  - pbi_identity_risk"
