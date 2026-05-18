# QA Kabul Checklist

## dbt

- [ ] `dbt build --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod` başarılı.
- [ ] `dbt docs generate --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod` başarılı.
- [ ] `fraud_project_raw` row-count testleri PASS.
- [ ] `fraud_project_mart` reconciliation testleri PASS.
- [ ] `fraud_project_powerbi` fact ve KPI testleri PASS.

## BigQuery

- [ ] `fraud_project_raw.train_transaction`: 590.540 satır.
- [ ] `fraud_project_raw.train_identity`: 144.233 satır.
- [ ] `fraud_project_raw.test_transaction`: 506.691 satır.
- [ ] `fraud_project_raw.test_identity`: 141.907 satır.
- [ ] `fraud_project_powerbi.fact_train_transactions`: 590.540 satır.
- [ ] `fraud_project_powerbi.pbi_executive_kpis`: 1 satır.
- [ ] `fraud_project_powerbi.pbi_quality_contract`: tüm satırlar PASS.

## Power BI

- [ ] `powerbi/fraud_project_v2.pbix` açılıyor.
- [ ] DirectQuery bağlantısı `workintech-working.fraud_project_powerbi` datasetine bağlı.
- [ ] 6 rapor sayfası var.
- [ ] Boş sayfa yok.
- [ ] Her sayfada en az 3 native visual var.
- [ ] Her visual veri gösteriyor.
- [ ] Yüzde, para ve sayı formatları doğru.
- [ ] Filtreler görselleri bozmayacak şekilde çalışıyor.
- [ ] Veri Kalitesi sayfasında kalite kontratı PASS görünüyor.

## Sunum

- [ ] Yönetici Özeti problemi 30 saniyede anlatıyor.
- [ ] Risk Konsantrasyonu sayfası Product C ve identity lift mesajını açık veriyor.
- [ ] Tutar ve Zaman sayfası drift anlatısını destekliyor.
- [ ] Ödeme ve Email sayfası operasyonel segmentleri gösteriyor.
- [ ] Model sayfası skorlamayı önceliklendirme katmanı olarak konumlandırıyor.
- [ ] Veri Kalitesi sayfası BigQuery/dbt lineage güvenini veriyor.

## Repo

- [ ] Credential JSON commitlenmedi.
- [ ] Ham Kaggle CSV commitlenmedi.
- [ ] DuckDB dosyası commitlenmedi.
- [ ] Büyük output dump klasörleri commitlenmedi.
- [ ] Görünür dokümanlarda geliştirme aracı veya yapay üretim izi yok.
