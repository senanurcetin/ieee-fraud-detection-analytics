# Full-source IEEE-CIS temporal and calibration acceptance evidence

> **SUPERSEDED RESEARCH MEASUREMENT:** These are the initial 17 October full-source results before same-timestamp SQL ties were deterministically ordered. Source CSV hashes match but row-order fingerprints differed between runners. Use the [canonical deterministically ordered full-source F03/F04 results](../research/KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md) for the latest empirical values. This dated record is retained for transparent provenance, not production metrics.


**Execution date:** 17 October 2026  
**Authorized run:** [GitHub Actions #39067832865](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39067832865) — both `temporal_hygiene` and `calibration` **SUCCESS**.  
**Source commit:** `58ca142dad7b36153ce3b584dc672c1431a6aca6` (one-time research branch based on prior green `main`).  
**Official Kaggle original train transactions:** 590,540. `train_transaction.csv` SHA-256: `3a5c83ab6b3cc13dcabe5ffa9f522307fd5f7f7b6e6f6a60c32284ca6283d642`; `train_identity.csv` SHA-256: `b63c725d8377be90a995268d97f347c17d456b95db45807adcf9f59cd603c37c`. No subset, raw competition rows or service-account keys uploaded.  
**Archive (7-day retention):** [F03 temporal artifact](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39067832865/artifacts/12113719067) and [F04 calibration artifact](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39067832865/artifacts/12114495556).

**Evidence status:** empirical, repeatable **offline research**, *not* live bank transactions, a production model, prospective calibration acceptance, or the source parity of 27 BigQuery report groups.

## F03 — Fit-window-only temporal hygiene

- Full population: 590,540; development 472,432; final chronological holdout 118,108; final fraud cases 4,064 (3.4409%).
- Same temporal splits, feature-preparation policy and 100-estimator LightGBM hyperparameters were used for ordinal codes versus native categorical handling.
- 425 features after fold-fit missingness screening, of which 339 V features and 26 categorical in this full-source run.
- Categorical vocabularies and V missingness rates were learned **only from each fit window**; unknown future categories map to sentinel missing values. Final holdout labels did not determine model preprocessing or queue thresholds.

| Independently held-out final 118,108 rows | Ordinal numeric codes | Native categorical |
|---|---:|---:|
| ROC-AUC ↑ | 0.895436 | **0.898614** |
| Average precision ↑ | 0.471524 | **0.477096** |
| Fit-derived p95 review workload | 5.3485% | **5.2029%** |
| Review queue precision | 34.6050% | **35.5574%** |
| Fraud capture at fit-derived p95 | **53.7894%** | 53.7648% |

**Interpretation:** Native categorical offers a small ROC-AUC/AP gain under this **100-tree controlled comparison**, but is not validated as superior to the previously published 500-tree historical model. The fit-only p95 threshold can select more or fewer than exactly 5% in later periods. These results **do not** update the dashboard or model registry.

One expanding development fold was executed. **Its initial training slice had only 10,000 rows, and its validation slice had 462,432 rows**; it is a diagnostic early-history stress test, not an adequate multi-fold temporal robustness assessment. The observed one-fold ROC-AUCs were 0.824222 ordinal and 0.808862 native. Do not average or market them as rolling five-fold CV.

## F04 — Disjoint temporal calibration

- Core model fit 354,324 rows (~60%), calibration-only middle 118,108 (~20%, **4,611 positive fraud cases**), untouched final evaluation 118,108 (~20%, **4,064 positives**).
- Strict boundaries: core max `TransactionDT=8745772`, calibration min `8745798`, calibration max `12192842`, final min `12192900`. No overlap.
- Independent 150-tree LightGBM; ordinal numeric categorical handling. Raw scores from class-weighted model are **not empirical fraud probabilities**.
- Platt/sigmoid logistic and isotonic mappings fitted **only on middle-window predictions and labels**. Final labels were not used to train calibrators. Constant baseline uses **core training prevalence** 0.0338334, not final holdout prevalence 0.0344092.

| Final holdout metric | Raw ranker | Platt/sigmoid | Isotonic | Constant core prior |
|---|---:|---:|---:|---:|
| ROC-AUC ↑ | **0.887296** | **0.887296** | 0.886938 | 0.500000 |
| Average precision ↑ | **0.464352** | **0.464352** | 0.448756 | 0.034409 |
| Brier ↓ | 0.099915 | 0.025139 | **0.023885** | 0.033226 |
| ECE (10 fixed bins) ↓ | 0.229358 | 0.013345 | 0.005996 | **0.000576** |
| Log loss ↓ | 0.344549 | 0.102341 | **0.100063** | 0.149755 |
| Mean output score | 0.263768 | 0.037959 | 0.037249 | 0.033833 |

**Interpretation:** Both calibration methods materially improve proper scoring rules relative to raw ranker predictions, with isotonic the lowest Brier/log loss of the two in this one final period. **However**, isotonic reduces average precision relative to raw/Platt (0.448756 vs 0.464352). The constant-prior baseline has the lowest ECE only because it predicts a nearly calibrated constant **without useful ranking information**; ECE alone cannot select a winning method. Real payment/credit decisions must not use any of these models without separate prospective checks and approval.

**Scientific limitations:**
1. This is a single locked temporal final holdout, not an external unseen future period after candidate selection. Use a future disjoint evaluation cohort before promoting a winner.
2. The selected 150-estimator calibrator is **not the same underlying model** as the historical published 500-estimator dashboard ranker. These calibration metrics cannot simply be copied onto that old model artifact.
3. The initial run reported Brier, ROC-AUC, AP, log loss, ECE and 10-bin reliability. The next opt-in code revision adds deterministic top-1%, top-5% and top-10% review-queue precision, capture and Wilson approximate 95% intervals; **those new metrics are NOT measured in the run above and must have their own exact-run evidence**.
4. Pooled/transaction-level Wilson intervals do not account for repeated card-profile or customer-level clustering; do not report them as prospective independent-cohort uncertainty.
5. No customer declines, automated operational actions, loss-avoidance claims, live source refresh, model promotion or Vercel deployment is authorized by these results.

## BigQuery provenance remains separate

The same one-shot run included a BigQuery WIF readiness check. **Neither**
`GCP_WIF_PROVIDER` nor `GCP_BIGQUERY_READONLY_SA` repository variable
was configured for the Fraud repo; the actual OIDC authentication and source
table reads were **skipped**. The BigQuery job exit status is green **only
because the no-credential path was explicitly treated as BLOCKED**, not
because it verified source parity. See [keyless WIF runbook](BIGQUERY_KAGGLE_WORKPLAN_2026-10-17.md), [source verification](../BIGQUERY_SOURCE_VERIFICATION_2026-10-15.md) and [issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9).

## Review and disposition

- [Issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8): full-source **new** random/time comparison and F03 experiment now observed; original missing publicly accessible Kaggle notebook remains separate.
- [Issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20): actual disjoint calibration completed, **production model promotion still open**, pending top-k new results, prospective robustness and model/feature scope review.
- [Issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9): BigQuery direct-table parity still unverified due to missing repo-scoped WIF config.
- [Issue #29](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/29): public Vercel exact-SHA release still a separate gate.

Both jobs ran on real Kaggle data without SQL jobs, snapshot edits or leaking source files; no raw predictions were uploaded.
