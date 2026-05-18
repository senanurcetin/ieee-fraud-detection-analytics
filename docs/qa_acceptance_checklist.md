# QA Kabul Checklist

Son doğrulama tarihi: 18 Mayıs 2026

## dbt

- [x] `dbt build --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod` başarılı.
- [x] Son build sonucu: `PASS=96 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=97`.
- [x] `dbt docs generate --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod` başarılı.
- [x] `fraud_project_raw` row-count testleri PASS.
- [x] `fraud_project_mart` reconciliation testleri PASS.
- [x] `fraud_project_powerbi` fact ve KPI testleri PASS.

## BigQuery

- [x] `fraud_project_raw.train_transaction`: 590.540 satır.
- [x] `fraud_project_raw.train_identity`: 144.233 satır.
- [x] `fraud_project_raw.test_transaction`: 506.691 satır.
- [x] `fraud_project_raw.test_identity`: 141.907 satır.
- [x] `fraud_project_staging.stg_transactions`: 590.540 satır.
- [x] `fraud_project_staging.stg_identity`: 144.233 satır.
- [x] `fraud_project_powerbi.fact_train_transactions`: 590.540 satır.
- [x] `fraud_project_powerbi.pbi_executive_kpis`: 1 satır.
- [x] `fraud_project_powerbi.pbi_quality_contract`: 6 satır.
- [x] `fraud_project_powerbi.pbi_segment_watchlist`: 20 satır.
- [x] `fraud_project_powerbi.pbi_review_strategy`: 4 satır.
- [x] `fraud_project_powerbi.pbi_threshold_simulation`: 16 satır.
- [x] `fraud_project_powerbi.pbi_report_readiness`: 6 satır.

## Power BI

- [x] `powerbi/fraud_project_v2.pbix` paket bütünlüğü PASS.
- [x] `SecurityBindings` paketten kaldırıldı.
- [x] 7 rapor sayfası var: 6 ana sunum sayfası + 1 canlı analitik kontrol sayfası.
- [x] Boş sayfa yok.
- [x] 46 visual container var.
- [x] 24 kayıtlı PNG analiz varlığı var.
- [x] Yeni yönetici görselleri rapor paketine gömülü.
- [x] `Canlı Analitik Katmanı` sayfasında 9 native query-bound visual var.
- [x] Native visual alanları dbt catalog kolonlarıyla eşleşiyor.
- [ ] Power BI Desktop içinde son görsel açılış kontrolü yapılmalı.
- [ ] DirectQuery yenilemesi sonrası native görsellerin veri döndürdüğü ekranda kontrol edilmeli.

## Sunum

- [x] Yönetici Özeti problemi ilk 30 saniyede anlatacak şekilde yapılandırıldı.
- [x] Risk Konsantrasyonu sayfası Product C ve identity lift mesajını veriyor.
- [x] Tutar ve Zaman sayfası drift anlatısını destekliyor.
- [x] Ödeme ve Email sayfası operasyonel segmentleri gösteriyor.
- [x] Model sayfası skorlamayı önceliklendirme katmanı olarak konumlandırıyor.
- [x] Veri Kalitesi sayfası BigQuery/dbt lineage güvenini veriyor.
- [x] Canlı Analitik Katmanı sayfası veri modeline bağlı kanıt sayfası olarak eklendi.

## Repo

- [x] Credential JSON commitlenmedi.
- [x] Ham Kaggle CSV commitlenmedi.
- [x] DuckDB dosyası commitlenmedi.
- [x] Büyük output dump klasörleri commitlenmedi.
- [x] Görünür dokümanlarda geliştirme aracı izi yok.
