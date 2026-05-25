# BigQuery ve dbt Lineage

## Katmanlar

```text
fraud_project_raw
  -> fraud_project_staging
  -> fraud_project_intermediate
  -> fraud_project_mart
  -> fraud_project_powerbi
```

## Raw Katmanı

Dataset: `fraud_project_raw`

Tablolar:

- `train_transaction`
- `train_identity`
- `test_transaction`
- `test_identity`
- `sample_submission`
- `feature_missingness`
- `ml_predictions`

Amaç: Ham Kaggle tablolarını ve model destek çıktılarını veri ambarında saklamak.

## Staging Katmanı

Dataset: `fraud_project_staging`

Modeller:

- `stg_transactions`
- `stg_identity`

Amaç: Ham alanları okunabilir isimlere çevirmek, veri tiplerini standartlaştırmak ve temel temizlik adımlarını uygulamak.

## Intermediate Katmanı

Dataset: `fraud_project_intermediate`

Modeller:

- `int_fraud_joined`
- `int_features`

Amaç: Transaction ve identity kayıtlarını birleştirmek, amount bandı, product, card, email, device ve zaman özelliklerini üretmek.

## Mart Katmanı

Dataset: `fraud_project_mart`

Modeller:

- `mart_fraud_summary`
- `mart_daily_stats`
- `mart_amount_bands`
- `mart_product_device_stats`
- `mart_email_domain_stats`
- `mart_feature_missingness`
- `mart_model_predictions`
- `mart_risk_band_stats`

Amaç: Fraud analizi, segment kıyasları, risk bandı izleme ve veri kalitesi için hazır analitik tablolar üretmek.

## Raporlama Katmanı

Dataset: `fraud_project_powerbi`

Tablolar:

- `fact_train_transactions`
- `mart_model_predictions`
- `mart_fraud_summary`
- `mart_daily_stats`
- `mart_amount_bands`
- `mart_product_device_stats`
- `mart_email_domain_stats`
- `mart_risk_band_stats`
- `mart_feature_missingness`
- `pbi_segment_watchlist`
- `pbi_review_strategy`
- `pbi_threshold_simulation`
- `pbi_feature_importance`
- `pbi_identity_product_coverage`
- `pbi_time_amount_signals`
- `pbi_report_readiness`
- `pbi_quality_contract`

Amaç: Canlı web dashboard içinde hızlı, güvenli ve sunuma hazır analitik veri modeli sağlamak.

## Testler

dbt test kapsamı:

- Transaction ID boş değer kontrolü
- Transaction ID benzersizlik kontrolü
- Fraud label kabul edilen değer kontrolü
- Günlük istatistiklerde gün benzersizliği
- Transaction amount boş değer kontrolü

Bu testler, raporlama katmanına geçmeden önce temel veri güvenilirliğini doğrular.
