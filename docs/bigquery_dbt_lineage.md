# BigQuery ve dbt Lineage

## Katmanlar

```text
fraud_project_raw
  -> fraud_project_staging
  -> fraud_project_intermediate
  -> fraud_project_mart
  -> fraud_project_reporting
```

## Raw KatmanÄ±

Dataset: `fraud_project_raw`

Tablolar:

- `train_transaction`
- `train_identity`
- `test_transaction`
- `test_identity`
- `sample_submission`
- `feature_missingness`
- `ml_predictions`

AmaÃ§: Ham Kaggle tablolarÄ±nÄ± ve model destek Ã§Ä±ktÄ±larÄ±nÄ± veri ambarÄ±nda saklamak.

## Staging KatmanÄ±

Dataset: `fraud_project_staging`

Modeller:

- `stg_transactions`
- `stg_identity`

AmaÃ§: Ham alanlarÄ± okunabilir isimlere Ã§evirmek, veri tiplerini standartlaÅŸtÄ±rmak ve temel temizlik adÄ±mlarÄ±nÄ± uygulamak.

## Intermediate KatmanÄ±

Dataset: `fraud_project_intermediate`

Modeller:

- `int_fraud_joined`
- `int_features`

AmaÃ§: Transaction ve identity kayÄ±tlarÄ±nÄ± birleÅŸtirmek, amount bandÄ±, product, card, email, device ve zaman Ã¶zelliklerini Ã¼retmek.

## Mart KatmanÄ±

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

AmaÃ§: Fraud analizi, segment kÄ±yaslarÄ±, risk bandÄ± izleme ve veri kalitesi iÃ§in hazÄ±r analitik tablolar Ã¼retmek.

## Raporlama KatmanÄ±

Dataset: `fraud_project_reporting`

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
- `rpt_segment_watchlist`
- `rpt_review_strategy`
- `rpt_threshold_simulation`
- `rpt_feature_importance`
- `rpt_identity_product_coverage`
- `rpt_time_amount_signals`
- `rpt_report_readiness`
- `rpt_quality_contract`

AmaÃ§: CanlÄ± web dashboard iÃ§inde hÄ±zlÄ±, gÃ¼venli ve sunuma hazÄ±r analitik veri modeli saÄŸlamak.

## Testler

dbt test kapsamÄ±:

- Transaction ID boÅŸ deÄŸer kontrolÃ¼
- Transaction ID benzersizlik kontrolÃ¼
- Fraud label kabul edilen deÄŸer kontrolÃ¼
- GÃ¼nlÃ¼k istatistiklerde gÃ¼n benzersizliÄŸi
- Transaction amount boÅŸ deÄŸer kontrolÃ¼

Bu testler, raporlama katmanÄ±na geÃ§meden Ã¶nce temel veri gÃ¼venilirliÄŸini doÄŸrular.
