# Power BI Yükleme Rehberi

Ana teslim dosyası:

```text
powerbi/fraud_project_v2.pbix
```

Bu dosya 6 sayfalık rapor layout'u ve mevcut Power BI veri modelini içerir.

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

Yüklenecek tablolar:

- `fact_train_transactions`
- `mart_model_predictions`
- `mart_fraud_summary`
- `mart_daily_stats`
- `mart_amount_bands`
- `mart_product_device_stats`
- `mart_email_domain_stats`
- `mart_risk_band_stats`
- `mart_feature_missingness`

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
Predicted Risk = AVERAGE(fact_train_transactions[predicted_fraud_probability])
High Risk Transactions =
CALCULATE([Transactions], fact_train_transactions[risk_band] IN {"High", "Critical"})
```
