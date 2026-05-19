# QA Kabul Checklist

Son doğrulama tarihi: 19 Mayıs 2026

## dbt

- [x] `dbt build --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod` başarılı.
- [x] Son build sonucu: `PASS=102 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=103`.
- [x] 29 model ve 73 data test bulundu.
- [x] `dbt docs generate --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target prod` başarılı.
- [x] `fraud_project_raw` row-count testleri PASS.
- [x] `fraud_project_mart` reconciliation testleri PASS.
- [x] Risk bandı monotonluk testi PASS.
- [x] Threshold simülasyonu monotonluk ve precision sinyal testleri PASS.
- [x] Segment watchlist iş kuralı testi PASS.
- [x] Review strategy iş kuralı testi PASS.
- [x] Power BI rapor kontratı testi PASS.

## BigQuery

- [x] `fraud_project_raw.train_transaction`: 590.540 satır.
- [x] `fraud_project_raw.train_identity`: 144.233 satır.
- [x] `fraud_project_raw.test_transaction`: 506.691 satır.
- [x] `fraud_project_raw.test_identity`: 141.907 satır.
- [x] `fraud_project_staging.stg_transactions`: 590.540 satır.
- [x] `fraud_project_staging.stg_identity`: 144.233 satır.
- [x] `fraud_project_intermediate.int_features`: 590.540 satır.
- [x] `fraud_project_mart.mart_risk_band_stats`: 8 satır.
- [x] `fraud_project_powerbi.fact_train_transactions`: 590.540 satır.
- [x] `fraud_project_powerbi.pbi_segment_watchlist`: 20 satır.
- [x] `fraud_project_powerbi.pbi_review_strategy`: 4 satır.
- [x] `fraud_project_powerbi.pbi_threshold_simulation`: 16 satır.
- [x] `fraud_project_powerbi.pbi_report_readiness`: 6 satır.

## Power BI

- [x] `powerbi/fraud_project_v2.pbix` paket bütünlüğü PASS.
- [x] `SecurityBindings` paketten kaldırıldı.
- [x] Final rapor 6 sunum sayfasından oluşuyor.
- [x] Ek teknik kontrol sayfası final rapordan kaldırıldı.
- [x] Boş sayfa yok.
- [x] 123 visual container var.
- [x] 29 query-bound native visual var.
- [x] Her sayfada en az 4 veri modeline bağlı native visual var.
- [x] 6 slicer var.
- [x] Gömülü görüntü visual sayısı 0.
- [x] Kayıtlı görsel kaynağı sayısı 0.
- [x] Kırılgan çizgi grafik ve tablo görseli kullanılmıyor.
- [x] Kullanılan veri alanlarının tamamı güvenli Power BI model allowlist'i içinde.
- [ ] Power BI Desktop içinde son görsel açılış kontrolü yapılmalı.
- [ ] DirectQuery yenilemesi sonrasında tüm görsellerin veri döndürdüğü ekranda kontrol edilmeli.

## Sunum

- [x] Yönetici Özeti problemi ilk 30 saniyede anlatacak şekilde yapılandırıldı.
- [x] Risk Konsantrasyonu sayfası product, device ve risk bandı kırılımlarını native görsellerle destekliyor.
- [x] Tutar ve Zaman sayfası tutar bandı, saat ve hacim analizini native görsellerle veriyor.
- [x] Ödeme ve Email sayfası operasyonel segmentleri native chart ve slicer yapısıyla gösteriyor.
- [x] Model sayfası skorlamayı önceliklendirme katmanı olarak konumlandırıyor.
- [x] Veri Kalitesi sayfası missingness, kalite kontrolü ve lineage anlatımını native metin ve görsellerle veriyor.
- [x] Her sayfada bulgu, risk, aksiyon veya kalite kapısı mesajları kısa karar panelleriyle görünür hale getirildi.
- [x] Görünür rapor içinde proje dışı üretim izi, geçici not veya sunum dışı teknik dil bulunmuyor.

## Repo

- [x] Credential JSON commitlenmedi.
- [x] Ham Kaggle CSV commitlenmedi.
- [x] DuckDB dosyası commitlenmedi.
- [x] Büyük output dump klasörleri commitlenmedi.
- [x] Görünür dokümanlarda geliştirme aracı izi yok.
