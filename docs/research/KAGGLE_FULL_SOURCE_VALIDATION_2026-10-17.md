# Full-source Kaggle validation: random vs chronological split

**Run date:** 17 October 2026  
**Study:** New reproducible random-vs-chronological IEEE-CIS holdout comparison  
**Execution:** [GitHub Actions run #39063907895](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39063907895) — `workflow_dispatch: random_vs_time`, **SUCCESS**  
**Exact reviewed Git SHA:** `763e1270257bfe3f79d918c04bdd613123da70d0`  
**Source CSV:** original Kaggle IEEE-CIS competition `train_transaction.csv`, SHA-256 `3a5c83ab6b3cc13dcabe5ffa9f522307fd5f7f7b6e6f6a60c32284ca6283d642`  
**Proof:** the run's output log and 7-day [sanitized artifact](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39063907895/artifacts/12112860358). No raw dataset, predictions or private keys were uploaded.

The Kaggle token and the official competition download were **actually validated** by the successful runner, rather than inferred from the presence of a GitHub secret.

## Reproducible experimental contract

- **Original training rows:** 590,540 (`subset_mode=false`).
- **Each split:** 472,432 fitting records; 118,108 independent holdout records.
- **Stratified random:** 80/20 shuffle, seed 42.
- **Chronological:** first 80% vs final 20% in relative `TransactionDT` order; identical timestamps do not cross the cutoff.
- **Algorithm:** LightGBM classifier, 150 estimators, seed 42 and fixed restricted numeric predictors (`TransactionAmt`, selected card/address/distance/count/time/V columns). Do **not** equate this with the separate historical 500-estimator/425-feature reporting model.
- **Environment:** Python 3.11.17; NumPy 2.4.6; pandas 2.2.3; LightGBM 4.6.0; scikit-learn 1.8.0.
- **Validation endpoint:** ranking performance only; no calibrated probability model, production promotion, client-level labels or live fraud detector.

## Observed full-data results

| Measure | Random holdout | Chronological holdout | Difference (random minus chronological) |
|---|---:|---:|---:|
| ROC-AUC | 0.920220 | 0.893140 | +0.027080 |
| Average precision | 0.619111 | 0.485269 | +0.133842 |
| Holdout fraud prevalence | 3.4993% | 3.4409% | +0.0584 pp |
| Train-known card-family proxy share of holdout | 96.5362% | 95.1527% | +1.3835 pp |
| Seen proxy ROC-AUC | 0.920417 | 0.893718 | +0.026699 |
| Seen proxy average precision | 0.620589 | 0.486025 | +0.134564 |
| Unseen proxy ROC-AUC | 0.915342 | 0.887664 | +0.027678 |
| Unseen proxy average precision | 0.579736 | 0.483416 | +0.096320 |

### Proxy cohort populations

| Holdout segment | Random n | Chronological n |
|---|---:|---:|
| Card-family proxy seen during fit | 114,017 | 112,383 |
| Card-family proxy not seen during fit | 4,091 | 5,725 |
| All holdout rows | 118,108 | 118,108 |

The masked card-family proxy combines card/address columns; it is **not** a verified person, customer or payment identity. Even the unseen subgroup shows worse chronological ranking than random ranking. This comparison can motivate follow-up research into time distribution shift, nonstationarity and account/card-like proxy recurrence, but **does not demonstrate causal target leakage**, prove cohort independence, estimate real transaction losses, or warrant immediate model replacement. Differences in holdout fraud prevalence matter especially when comparing average precision.

## What this does and does not close

**Completed:** The repository's new random-versus-time experiment has now been run on an independently downloaded original full Kaggle competition source. Its exact input digest, source SHA, dependencies, splits and measured metrics are tied to GitHub Actions evidence.

**Subsequent evidence:** Full-source temporal hygiene and disjoint calibration research also completed on 17 October; see [canonical deterministic results](KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md). The earlier instruction to run F03/F04 next is superseded.

**Remaining:** Recovery of the original notebook is not established. Publication of the replacement on Kaggle requires separate execution and a verified URL. Model promotion requires a matched base model and independent validation; BigQuery parity remains a separate gate. Current production checks and access are recorded in [release status](../RELEASE_STATUS.md). This research run does not refresh the dashboard snapshot.
