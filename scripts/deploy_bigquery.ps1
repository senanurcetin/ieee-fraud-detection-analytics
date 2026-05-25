param(
    [Parameter(Mandatory = $true)]
    [string]$Credentials,

    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Location = "US",
    [string]$ReportingDataset = "fraud_project_reporting"
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

Write-Host ""
Write-Host "BigQuery deployment complete."
Write-Host "Reporting dataset: $ProjectId.$ReportingDataset"
Write-Host "Recommended tables:"
Write-Host "  - fact_train_transactions"
Write-Host "  - rpt_executive_kpis"
Write-Host "  - rpt_product_risk"
Write-Host "  - rpt_identity_risk"
Write-Host "  - rpt_segment_watchlist"
Write-Host "  - rpt_threshold_simulation"
Write-Host "  - rpt_report_readiness"
