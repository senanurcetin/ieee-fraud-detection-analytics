# 02 - Tech-Stack

## Mimari AkÄ±ÅŸ

```text
Kaggle CSV
  -> BigQuery raw dataset
  -> dbt staging
  -> dbt intermediate
  -> dbt mart
  -> fraud_project_reporting
  -> FastAPI web dashboard / Vercel sunumu
```

## Veri AlÄ±mÄ±

- Kaynak: IEEE-CIS Fraud Detection Kaggle CSV dosyalarÄ±
- Ham tablolar: `train_transaction`, `train_identity`, `test_transaction`, `test_identity`, `sample_submission`
- YÃ¼kleme hedefi: `fraud_project_raw`

## Veri AmbarÄ±

BigQuery tarafÄ±nda aÅŸaÄŸÄ±daki dataset yapÄ±sÄ± kullanÄ±lÄ±r:

- `fraud_project_raw`
- `fraud_project_staging`
- `fraud_project_intermediate`
- `fraud_project_mart`
- `fraud_project_reporting`

Bu ayrÄ±m, ham veri, dÃ¶nÃ¼ÅŸÃ¼m katmanÄ±, analitik mart ve raporlama katmanÄ±nÄ± birbirinden ayÄ±rÄ±r.

## dbt

dbt projesi repo kÃ¶kÃ¼nde Ã§alÄ±ÅŸÄ±r.

```powershell
dbt run --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod
dbt test --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod
```

Model katmanlarÄ±:

- `models/staging`: Alan adlarÄ±, veri tipi dÃ¶nÃ¼ÅŸÃ¼mÃ¼, temel temizlik
- `models/intermediate`: Transaction ve identity join'i, feature Ã¼retimi
- `models/marts`: Fraud metrikleri, segment tablolarÄ±, model skorlarÄ± ve risk bantlarÄ±

## Makine Ã–ÄŸrenmesi

- Model: LightGBMClassifier
- DoÄŸrulama: TransactionDT sÄ±ralamasÄ±na gÃ¶re son %20 holdout
- Feature sayÄ±sÄ±: 206
- Kategorik feature sayÄ±sÄ±: 26
- Validasyon AUC: 0,917
- Average precision: 0,531

Model Ã§Ä±ktÄ±larÄ± `mart_model_predictions` ve `mart_risk_band_stats` tablolarÄ±yla raporlama katmanÄ±na taÅŸÄ±nÄ±r.

## CanlÄ± Web Dashboard

Ana sunum katmanÄ±:

```text
webapp/
```

Dashboard, `fraud_project_reporting` datasetindeki fact, mart ve `rpt_*` tablolarÄ±nÄ± FastAPI Ã¼zerinden okur. ArayÃ¼z; yÃ¶netici KPI'larÄ±, global slicer'lar, drill-through paneli, Ã¶zel tooltip'ler, Pareto analizi, decomposition tree, identity coverage matrisi, threshold simÃ¼lasyonu ve veri kalite kartlarÄ±yla Ã¼st yÃ¶netim sunumunda doÄŸrudan kullanÄ±lacak ÅŸekilde hazÄ±rlanmÄ±ÅŸtÄ±r.

## GÃ¼venlik ve Versiyonlama

- Servis hesabÄ± JSON dosyasÄ± repoya eklenmez.
- Ham Kaggle CSV dosyalarÄ± repoya eklenmez.
- DuckDB ve geÃ§ici output dosyalarÄ± repoya eklenmez.
- Repo yalnÄ±zca kaynak kod, dbt modelleri, canlÄ± web dashboard ve dokÃ¼mantasyonu iÃ§erir.
