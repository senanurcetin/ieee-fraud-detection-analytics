# 02 - Tech-Stack

## Mimari Akış

```text
Kaggle CSV
  -> BigQuery raw dataset
  -> dbt staging
  -> dbt intermediate
  -> dbt mart
  -> fraud_project_powerbi
  -> FastAPI web dashboard / Vercel sunumu
```

## Veri Alımı

- Kaynak: IEEE-CIS Fraud Detection Kaggle CSV dosyaları
- Ham tablolar: `train_transaction`, `train_identity`, `test_transaction`, `test_identity`, `sample_submission`
- Yükleme hedefi: `fraud_project_raw`

## Veri Ambarı

BigQuery tarafında aşağıdaki dataset yapısı kullanılır:

- `fraud_project_raw`
- `fraud_project_staging`
- `fraud_project_intermediate`
- `fraud_project_mart`
- `fraud_project_powerbi`

Bu ayrım, ham veri, dönüşüm katmanı, analitik mart ve raporlama katmanını birbirinden ayırır.

## dbt

dbt projesi repo kökünde çalışır.

```powershell
dbt run --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod
dbt test --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod
```

Model katmanları:

- `models/staging`: Alan adları, veri tipi dönüşümü, temel temizlik
- `models/intermediate`: Transaction ve identity join'i, feature üretimi
- `models/marts`: Fraud metrikleri, segment tabloları, model skorları ve risk bantları

## Makine Öğrenmesi

- Model: LightGBMClassifier
- Doğrulama: TransactionDT sıralamasına göre son %20 holdout
- Feature sayısı: 206
- Kategorik feature sayısı: 26
- Validasyon AUC: 0,917
- Average precision: 0,531

Model çıktıları `mart_model_predictions` ve `mart_risk_band_stats` tablolarıyla raporlama katmanına taşınır.

## Canlı Web Dashboard

Ana sunum katmanı:

```text
webapp/
```

Dashboard, `fraud_project_powerbi` datasetindeki fact, mart ve `pbi_*` tablolarını FastAPI üzerinden okur. Arayüz; yönetici KPI'ları, global slicer'lar, drill-through paneli, özel tooltip'ler, Pareto analizi, decomposition tree, identity coverage matrisi, threshold simülasyonu ve veri kalite kartlarıyla üst yönetim sunumunda doğrudan kullanılacak şekilde hazırlanmıştır.

Arşivlenen Power BI prototipi `powerbi/fraud_project_v2.pbix` altında korunur; ana raporlama teslimi değildir.

## Güvenlik ve Versiyonlama

- Servis hesabı JSON dosyası repoya eklenmez.
- Ham Kaggle CSV dosyaları repoya eklenmez.
- DuckDB ve geçici output dosyaları repoya eklenmez.
- Repo yalnızca kaynak kod, dbt modelleri, canlı web dashboard, arşivlenmiş BI prototipi ve dokümantasyonu içerir.
