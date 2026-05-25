# QA Kabul Checklist

Son doğrulama hedefi: canlı web dashboard ana sunum katmanıdır. Power BI dosyası yalnızca arşivlenmiş prototip olarak korunur.

## dbt

- [x] `dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod` başarılı.
- [x] Son doğrulanmış build sonucu: `PASS=123 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=124`.
- [x] Veri seti metodoloji genişletmesi sonrası tam build: 33 model ve 90 data test.
- [x] `dbt docs generate --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod` başarılı.
- [x] `fraud_project_raw` row-count testleri PASS.
- [x] `fraud_project_mart` reconciliation testleri PASS.
- [x] Risk bandı monotonluk testi PASS.
- [x] Threshold simülasyonu monotonluk ve precision sinyal testleri PASS.
- [x] Segment watchlist iş kuralı testi PASS.
- [x] Review strategy iş kuralı testi PASS.
- [x] Web raporlama kontratı testi PASS.

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
- [x] `fraud_project_powerbi.pbi_identity_product_coverage`: ProductCD bazında 5 satır.
- [x] `fraud_project_powerbi.pbi_time_amount_signals`: relatif saat ve tutar-decimal kırılımında 48 satır.
- [x] `fraud_project_powerbi.pbi_quality_contract`: 6 kalite kapısı.

## Canlı Web Dashboard

- [x] Ana sunum URL'i: `https://fraud-project-web.vercel.app`.
- [x] API endpoint: `/api/dashboard`.
- [x] API yalnızca `fraud_project_powerbi` raporlama tablolarını okur.
- [x] Dashboard payload kontratı 18 tabloyu kapsar.
- [x] Global slicer'lar: metrik, segment ailesi, operasyon önceliği.
- [x] Drill-through paneli seçilen segment için detay ve aksiyon gösterir.
- [x] Özel tooltip katmanı bar, heatmap, time series ve model eğrilerinde çalışır.
- [x] Pareto grafiği fraud katkısını kümülatif olarak gösterir.
- [x] Decomposition tree segment risk sürücülerini sunar.
- [x] Identity/product coverage matrisi veri kapsamı ile fraud riskini birlikte gösterir.
- [x] Relatif saat ve amount-decimal heatmap davranışsal zaman/tutar sinyallerini gösterir.
- [x] Threshold simülasyonu workload, capture ve precision etkisini gösterir.
- [x] Feature importance ve feature-family treemap model sinyallerini açıklar.
- [x] Veri kalite kontratı ve readiness scorecard sunuma hazırdır.

## Sunum

- [x] Yönetici özeti ilk 30 saniyede problemi ve aksiyon alanını anlatır.
- [x] Segment analizi ProductCD, identity, payment, email ve amount kırılımlarını karşılaştırır.
- [x] Model bölümü skorlamayı karar motoru değil, önceliklendirme katmanı olarak konumlandırır.
- [x] Veri güveni bölümü dbt, BigQuery ve raporlama katmanının kalite kanıtını gösterir.
- [x] Görünür rapor içinde geliştirme aracı izi, geçici not veya sunum dışı teknik dil bulunmaz.

## Repo

- [x] Credential JSON commitlenmedi.
- [x] Ham Kaggle CSV commitlenmedi.
- [x] DuckDB dosyası commitlenmedi.
- [x] Büyük output dump klasörleri commitlenmedi.
- [x] Görünür dokümanlarda geliştirme aracı izi yok.
