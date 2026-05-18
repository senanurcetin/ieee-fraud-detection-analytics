# BigQuery Deployment

Bu proje BigQuery üzerinde çalışacak şekilde hazırlanmıştır. Komutları çalıştırmadan önce kimlik bilgileri ve proje ayarları yapılandırılmalıdır.

## Gerekli Ortam Değişkenleri

```powershell
$env:GCP_PROJECT_ID="workintech-working"
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
$env:BIGQUERY_LOCATION="US"
```

## Ham Tabloları Yükleme

```powershell
python src\upload_to_bigquery.py
```

Loader aşağıdaki datasetleri oluşturur:

- `raw`
- `staging`
- `intermediate`
- `mart`
- `dbt_default`

Ardından dbt modelleri BigQuery hedefiyle çalıştırılabilir:

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" run --project-dir dbt_ieee_fraud --profiles-dir profiles --profile ieee_fraud_detection --target prod
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" test --project-dir dbt_ieee_fraud --profiles-dir profiles --profile ieee_fraud_detection --target prod
```

## Operasyonel Notlar

- `maximum_bytes_billed` değeri profil dosyasında açık tutulmalıdır.
- BI raporlamasında önce mart tabloları kullanılmalıdır.
- Ham transaction tabloları çok geniş kolon yapısına sahip olduğu için doğrudan rapor katmanında taranmamalıdır.
- Kaggle ham veri dosyaları GitHub'a yüklenmemelidir.
