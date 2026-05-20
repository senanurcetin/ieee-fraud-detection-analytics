# BigQuery Deployment

Bu proje BigQuery üzerinde `fraud_project` adıyla katmanlı bir analitik mimari kurar. Deployment scripti ham CSV yüklemesini, dbt dönüşümlerini, testleri ve Power BI raporlama tablolarını tek akışta çalıştırır.

## Dataset Yapısı

- `fraud_project_raw`
- `fraud_project_staging`
- `fraud_project_intermediate`
- `fraud_project_mart`
- `fraud_project_powerbi`

## Komut

```powershell
.\scripts\deploy_bigquery.ps1 `
  -Credentials $env:GOOGLE_APPLICATION_CREDENTIALS `
  -ProjectId $env:GCP_PROJECT_ID `
  -Location "US" `
  -ReportingDataset "fraud_project_powerbi"
```

## dbt Komutları

```powershell
dbt run --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod
dbt test --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod
```

## Power BI Raporlama Katmanı

`fraud_project_powerbi` datasetinde aşağıdaki tablolar oluşturulur:

- `fact_train_transactions`
- `mart_model_predictions`
- `mart_fraud_summary`
- `mart_daily_stats`
- `mart_amount_bands`
- `mart_product_device_stats`
- `mart_email_domain_stats`
- `mart_risk_band_stats`
- `mart_feature_missingness`

## Minimum Yetkiler

Servis hesabı için gerekli minimum BigQuery rolleri:

- BigQuery Job User
- BigQuery Data Editor
- BigQuery Data Viewer

## Operasyonel Notlar

- Ham transaction tabloları çok geniş kolon yapısına sahiptir; raporlama için doğrudan ham katman yerine mart ve Power BI datasetleri kullanılmalıdır.
- `fraud_project_powerbi` katmanı, Power BI Desktop içinde sade ve yönetilebilir bir model oluşturmak için özetlenmiş tablolardan oluşur.
- Servis hesabı JSON dosyası repoya eklenmez.
