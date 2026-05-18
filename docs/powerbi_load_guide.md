# Power BI Yükleme Rehberi

`.pbit` dosyası Power BI Desktop sürüm veya paketleme farkı nedeniyle açılmazsa ana yöntem olarak BigQuery ya da CSV klasör bağlantısını kullanın.

## Seçenek 1: BigQuery Üzerinden Açma

Önce BigQuery yüklemesini çalıştırın:

```powershell
.\scripts\deploy_bigquery.ps1 -Credentials "C:\path\to\service-account.json" -ProjectId "workintech-working" -Location "US" -ReportingDataset "powerbi"
```

Bu komut ham tabloları BigQuery'ye yükler, dbt modellerini BigQuery üzerinde çalıştırır ve Power BI için hazır raporlama tablolarını `workintech-working.powerbi` datasetine yazar.

Power BI Desktop içinde:

1. `Get Data` > `Google BigQuery` seçin.
2. Google hesabı veya servis hesabı ile giriş yapın.
3. `workintech-working` projesini açın.
4. `powerbi` datasetini seçin.
5. `fact_train_transactions` ve `mart_*` tablolarını `Import` modu ile yükleyin.

Önerilen ilişki:

- `fact_train_transactions[transaction_id]` -> `mart_model_predictions[transaction_id]`

## Seçenek 2: Lokal CSV Klasöründen Açma

Power BI Desktop ile şu dosyayı açın:

`outputs/powerbi/ieee_fraud_csv_folder.pbids`

Navigator ekranında CSV dosyaları görünecektir. Tabloları seçip `Load` veya `Transform Data` ile içeri alın.

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
