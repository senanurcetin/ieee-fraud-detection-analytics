# IEEE-CIS Fraud Detection Analytics Project

Kaggle IEEE-CIS Fraud Detection veri seti üzerinde hazırlanmış profesyonel fraud analizi, veri modelleme, model skorlama, Power BI raporlama ve sunum teslim paketidir.

Projenin ana hikayesi analiz odaklıdır: sahtecilik nadir görülür, ancak ürün ailesi, identity kaydı, ödeme tipi, email domain, işlem tutarı ve zaman kırılımlarında belirgin şekilde yoğunlaşır. Model skorları, bu segmentleri BI tarafında önceliklendirilebilir inceleme kuyruklarına dönüştürmek için kullanılır.

## Proje Kapsamı

- Veri ambarı: DuckDB tabanlı analitik model
- Dönüşüm: dbt staging, intermediate ve mart katmanları
- Modelleme: LightGBM skorlaması ve zamana dayalı doğrulama
- BI teslimi: Power BI uyumlu CSV martları ve PBIT template
- Sunum: düzenlenebilir PowerPoint analitik vaka çalışması

Ham Kaggle verileri GitHub'a eklenmez. Repo yalnızca kod, modelleme katmanı, dokümantasyon ve yeniden üretilebilir proje yapısını içerir.

## Veri Setini Hazırlama

`C:\Users\MONSTER\Downloads\ieee-fraud-detection.zip` dosyası yoksa Kaggle indirme scriptlerinden biri kullanılabilir:

```powershell
.\scripts\download_kaggle.ps1
```

```bash
./scripts/download_kaggle.sh
```

## Çalıştırma

```powershell
python src\prepare_raw_and_ml.py
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" run --project-dir dbt_ieee_fraud --profiles-dir profiles
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" test --project-dir dbt_ieee_fraud --profiles-dir profiles
python src\export_powerbi_and_charts.py
python src\create_powerbi_template.py
python src\build_presentation_deck.py
```

Power BI template:

`outputs/powerbi/ieee_fraud_detection_dashboard.pbit`

Düzenlenebilir PowerPoint sunumu:

`outputs/presentation/ieee-cis-fraud-detection-analysis.pptx`

Analiz hikayesi:

`outputs/tables/analysis_story.md`

## BigQuery

Proje BigQuery yükleme scriptleri ve dbt profil şablonlarıyla birlikte gelir. Otomatik yükleme için servis hesabı JSON dosyası veya Application Default Credentials yapılandırması gerekir.
