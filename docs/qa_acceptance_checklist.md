# QA Kabul Checklist

Son doÄŸrulama hedefi: canlÄ± web dashboard ana sunum katmanÄ±dÄ±r.

## dbt

- [x] `dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod` baÅŸarÄ±lÄ±.
- [x] Son doÄŸrulanmÄ±ÅŸ build sonucu: `PASS=123 WARN=0 ERROR=0 SKIP=0 NO-OP=1 TOTAL=124`.
- [x] Veri seti metodoloji geniÅŸletmesi sonrasÄ± tam build: 33 model ve 90 data test.
- [x] `dbt docs generate --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod` baÅŸarÄ±lÄ±.
- [x] `fraud_project_raw` row-count testleri PASS.
- [x] `fraud_project_mart` reconciliation testleri PASS.
- [x] Risk bandÄ± monotonluk testi PASS.
- [x] Threshold simÃ¼lasyonu monotonluk ve precision sinyal testleri PASS.
- [x] Segment watchlist iÅŸ kuralÄ± testi PASS.
- [x] Review strategy iÅŸ kuralÄ± testi PASS.
- [x] Web raporlama kontratÄ± testi PASS.

## BigQuery

- [x] `fraud_project_raw.train_transaction`: 590.540 satÄ±r.
- [x] `fraud_project_raw.train_identity`: 144.233 satÄ±r.
- [x] `fraud_project_raw.test_transaction`: 506.691 satÄ±r.
- [x] `fraud_project_raw.test_identity`: 141.907 satÄ±r.
- [x] `fraud_project_staging.stg_transactions`: 590.540 satÄ±r.
- [x] `fraud_project_staging.stg_identity`: 144.233 satÄ±r.
- [x] `fraud_project_intermediate.int_features`: 590.540 satÄ±r.
- [x] `fraud_project_mart.mart_risk_band_stats`: 8 satÄ±r.
- [x] `fraud_project_reporting.fact_train_transactions`: 590.540 satÄ±r.
- [x] `fraud_project_reporting.rpt_segment_watchlist`: 20 satÄ±r.
- [x] `fraud_project_reporting.rpt_review_strategy`: 4 satÄ±r.
- [x] `fraud_project_reporting.rpt_threshold_simulation`: 16 satÄ±r.
- [x] `fraud_project_reporting.rpt_report_readiness`: 6 satÄ±r.
- [x] `fraud_project_reporting.rpt_identity_product_coverage`: ProductCD bazÄ±nda 5 satÄ±r.
- [x] `fraud_project_reporting.rpt_time_amount_signals`: relatif saat ve tutar-decimal kÄ±rÄ±lÄ±mÄ±nda 48 satÄ±r.
- [x] `fraud_project_reporting.rpt_quality_contract`: 6 kalite kapÄ±sÄ±.

## CanlÄ± Web Dashboard

- [x] Ana sunum URL'i: `https://fraud-project-web.vercel.app`.
- [x] API endpoint: `/api/dashboard`.
- [x] API yalnÄ±zca `fraud_project_reporting` raporlama tablolarÄ±nÄ± okur.
- [x] Dashboard payload kontratÄ± 18 tabloyu kapsar.
- [x] Global slicer'lar: metrik, segment ailesi, operasyon Ã¶nceliÄŸi.
- [x] Drill-through paneli seÃ§ilen segment iÃ§in detay ve aksiyon gÃ¶sterir.
- [x] Ã–zel tooltip katmanÄ± bar, heatmap, time series ve model eÄŸrilerinde Ã§alÄ±ÅŸÄ±r.
- [x] Pareto grafiÄŸi fraud katkÄ±sÄ±nÄ± kÃ¼mÃ¼latif olarak gÃ¶sterir.
- [x] Decomposition tree segment risk sÃ¼rÃ¼cÃ¼lerini sunar.
- [x] Identity/product coverage matrisi veri kapsamÄ± ile fraud riskini birlikte gÃ¶sterir.
- [x] Relatif saat ve amount-decimal heatmap davranÄ±ÅŸsal zaman/tutar sinyallerini gÃ¶sterir.
- [x] Threshold simÃ¼lasyonu workload, capture ve precision etkisini gÃ¶sterir.
- [x] Feature importance ve feature-family treemap model sinyallerini aÃ§Ä±klar.
- [x] Veri kalite kontratÄ± ve readiness scorecard sunuma hazÄ±rdÄ±r.

## Sunum

- [x] YÃ¶netici Ã¶zeti ilk 30 saniyede problemi ve aksiyon alanÄ±nÄ± anlatÄ±r.
- [x] Segment analizi ProductCD, identity, payment, email ve amount kÄ±rÄ±lÄ±mlarÄ±nÄ± karÅŸÄ±laÅŸtÄ±rÄ±r.
- [x] Model bÃ¶lÃ¼mÃ¼ skorlamayÄ± karar motoru deÄŸil, Ã¶nceliklendirme katmanÄ± olarak konumlandÄ±rÄ±r.
- [x] Veri gÃ¼veni bÃ¶lÃ¼mÃ¼ dbt, BigQuery ve raporlama katmanÄ±nÄ±n kalite kanÄ±tÄ±nÄ± gÃ¶sterir.
- [x] GÃ¶rÃ¼nÃ¼r rapor iÃ§inde geliÅŸtirme aracÄ± izi, geÃ§ici not veya sunum dÄ±ÅŸÄ± teknik dil bulunmaz.

## Repo

- [x] Credential JSON commitlenmedi.
- [x] Ham Kaggle CSV commitlenmedi.
- [x] DuckDB dosyasÄ± commitlenmedi.
- [x] BÃ¼yÃ¼k output dump klasÃ¶rleri commitlenmedi.
- [x] GÃ¶rÃ¼nÃ¼r dokÃ¼manlarda geliÅŸtirme aracÄ± izi yok.
