# Power BI Yükleme Rehberi

Ana teslim dosyası:

```text
powerbi/fraud_project_v2.pbix
```

Bu dosya 6 sunum sayfası ve mevcut Power BI DirectQuery veri modelini içerir.

## BigQuery Üzerinden Yenileme

Önce BigQuery deployment çalıştırılır:

```powershell
.\scripts\deploy_bigquery.ps1 `
  -Credentials "C:\Users\MONSTER\Downloads\workintech-working-2378ce4f85e2.json" `
  -ProjectId "workintech-working" `
  -Location "US" `
  -ReportingDataset "fraud_project_powerbi"
```

Power BI Desktop içinde Google BigQuery bağlantısı kullanılırken hedef dataset:

```text
workintech-working.fraud_project_powerbi
```

## Ana Rapor Tabloları

- `fact_train_transactions`
- `mart_fraud_summary`
- `mart_amount_bands`
- `mart_email_domain_stats`
- `mart_product_device_stats`
- `mart_risk_band_stats`
- `mart_feature_missingness`

## BigQuery Raporlama Katmanı

dbt tarafında aşağıdaki Power BI destek tabloları da üretilir. Power BI model metadata'sı yenilendiğinde bu tablolar rapora kontrollü şekilde eklenebilir:

- `pbi_executive_kpis`
- `pbi_product_risk`
- `pbi_identity_risk`
- `pbi_amount_bands`
- `pbi_daily_drift`
- `pbi_payment_heatmap`
- `pbi_email_domain_risk`
- `pbi_model_risk_bands`
- `pbi_feature_importance`
- `pbi_data_quality_scorecard`
- `pbi_report_narrative`
- `pbi_quality_contract`
- `pbi_segment_watchlist`
- `pbi_review_strategy`
- `pbi_threshold_simulation`
- `pbi_report_readiness`

## Önerilen İlişki

```text
fact_train_transactions[transaction_id]
  -> mart_model_predictions[transaction_id]
```

## Önerilen DAX Ölçüleri

```DAX
Transactions = COUNTROWS(fact_train_transactions)
Fraud Transactions = SUM(fact_train_transactions[is_fraud])
Fraud Rate = DIVIDE([Fraud Transactions], [Transactions])
Average Amount = AVERAGE(fact_train_transactions[transaction_amount])
High Risk Transactions =
CALCULATE([Transactions], fact_train_transactions[risk_band] IN {"High", "Critical"})
```
