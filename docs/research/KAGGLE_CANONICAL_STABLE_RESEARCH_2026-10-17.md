# Canonical 17 October 2026 IEEE-CIS research — stable source order and full data

> **20 October update:** The original notebook source and its prior completed provider run have now been recovered and its public page verified. See [recovery and publication evidence](KAGGLE_RECOVERY_2026-10-20.md). Earlier missing-notebook statements below describe the historical state; they do not establish current unavailability.

**Scientific acceptance type:** bounded historical, independent temporal holdout research; **not** current bank monitoring or production calibrated-model sign-off.

## Immutable source and code evidence

- [Full-source stable replay #39069399816](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816) — **SUCCESS** for `temporal_hygiene` and `calibration` jobs, each in a separate runner using the same immutable source code.
- Research commit: `08753818f740b6b46351500620c8418035bfad83` (one-shot workflow file only, based on merge commit `6dbf2b088303262b533162d720ea685515ebecfd`).
- `train_transaction.csv` original Kaggle SHA-256: `3a5c83ab6b3cc13dcabe5ffa9f522307fd5f7f7b6e6f6a60c32284ca6283d642`; `train_identity.csv` SHA-256: `b63c725d8377be90a995268d97f347c17d456b95db45807adcf9f59cd603c37c`.
- **Data rows:** 590,540 original training transactions, `subset_mode=false`. No source CSVs, original transaction-level data, identity records or secrets were committed/uploaded.
- **Verified identical stable row fingerprint across independent F03 and F04 runners:** `a88c50af02f916b2c926752a7e7cb14da6cda988e563cc98588ae78fbab73335`, calculated from ordered `TransactionID`, `TransactionDT`, `isFraud` rows.
- Input read is reproducibly ordered by **`TransactionDT`, `TransactionID`** for opt-in research. The historical 500-estimator publishing pipeline's default SQL and published web snapshots are unchanged.
- [F03 sanitized metrics artifact](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816/artifacts/12113654772), [F04 sanitized calibration artifact](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39069399816/artifacts/12114661723) — only hash and aggregate result JSON; GitHub retention 7 days.

### Why the previous experimental measurements differ

Prior successful full-source studies [#39067832865](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39067832865)
and [#39068827927](https://github.com/senanurcetin/ieee-fraud-detection-analytics/actions/runs/39068827927)
reported the **same CSV input SHA**, but their `TransactionID/TransactionDT/isFraud`
row-order fingerprints differed (due to unspecified relative ordering of equal
`TransactionDT` records). Even exact input records can therefore produce slightly
different measured values when model fitting or score-tie handling depends on
record ordering. PR [#41](https://github.com/senanurcetin/ieee-fraud-detection-analytics/pull/41)
fixed this by adding an **opt-in** `stable_ties=True` research SQL flag and
synthetic tests. **Use this page's stable measurements as the current canonical
empirical values.** The older experimental reports remain dated, inspectable
evidence, not deleted/falsely re-labeled artifacts.

## F03 — Chronological temporal hygiene with fold-fit preprocessing

| Source/method contract | Ordinal numeric coding | Native LightGBM categorical |
|---|---:|---:|
| Core training/development rows | 472,432 | 472,432 |
| Untouched later holdout rows | 118,108 | 118,108 |
| LightGBM estimators | 100 | 100 |
| Fit-selected predictors | 425 | 425 |
| ROC-AUC ↑ | 0.895158 | **0.897345** |
| Average precision ↑ | 0.470195 | **0.471734** |
| Fit-derived p95 review workload | 5.5331% | 5.2977% |
| Fit-derived p95 review precision | 33.5731% | **35.0328%** |
| Fraud capture at fit-derived p95 | 53.9862% | 53.9370% |

Time splits, categorical vocabulary and V missingness selection were
independent of final holdout values and labels. Both methods had the same
features and chronological split, allowing an internal comparison.
This run still used only **one** development fold with first 10,000 training
records and 462,432 validation records, so it is **not 5-fold or
production-quality rolling temporal CV**. Model performance is not identical
to the historical deployed 500-estimator model or the prior 150-estimator
limited-feature random-time split comparison.

## F04 — Calibration on separate core, middle and final periods

**Splits:** core fit 354,324 rows; calibration-only 118,108 rows (4,611 positives);
strictly later untouched final test 118,108 rows (4,064 positives,
3.4409% prevalence). Feature count 425; ordinal LightGBM 150 estimators.

Calibrators were fit only on **middle-period** base model scores and fraud
labels, never on final-period labels. The constant baseline is the core-period
fraud prior, not the final observed rate. The report is a descriptive
research comparison on a single final period, not an endorsement of any
calibrator for prospective bank transaction decisions.

| Metric | Uncalibrated ranker | Platt/sigmoid | Isotonic | Core prior |
|---|---:|---:|---:|---:|
| ROC-AUC ↑ | **0.888649** | **0.888649** | 0.888287 | 0.500000 |
| Average precision ↑ | **0.466024** | **0.466024** | 0.452883 | 0.034409 |
| Brier ↓ | 0.098584 | 0.025114 | **0.023874** | 0.033226 |
| ECE (10 fixed bins) ↓ | 0.226695 | 0.013179 | 0.005806 | **0.000576** |

The constant-core-prior predictor's tiny ECE is **not** useful
discrimination (ROC-AUC 0.5). Isotonic yields the lowest observed Brier
of the learned predictors but a lower AP than Platt/raw. The Platt transform
preserves the underlying raw ranking; isotonic creates ties and can change
ranking. These findings cannot be retrofitted to the separately published
500-estimator model's output contract.

### Fixed-capacity review queues, measured on final temporal holdout

Deterministic score ranking chooses records **without consulting their
true fraud label**; exact top-k capacity is determined before inspection.
Wilson confidence bands in the retained JSON artifact are only approximate
transaction-level binomial intervals, **not** cluster-robust or prospective
uncertainty bounds.

| Method | Queue | Reviewed | Fraud captured | Precision | Approx. Wilson 95% precision interval | Fraud recall | Lift vs 3.4409% |
|---|---|---:|---:|---:|---:|---:|---:|
| Isotonic | Top 1% | 1,182 | 1,026 | 86.802% | 84.753–88.613% | 25.246% | 25.23x |
| Isotonic | Top 5% | 5,906 | 2,039 | 34.524% | 33.322–35.747% | 50.172% | 10.03x |
| Isotonic | Top 10% | 11,811 | 2,632 | 22.284% | 21.543–23.044% | 64.764% | 6.48x |
| Platt | Top 1% | 1,182 | 1,026 | 86.802% | 84.753–88.613% | 25.246% | 25.23x |
| Platt | Top 5% | 5,906 | 2,041 | 34.558% | 33.356–35.781% | 50.221% | 10.04x |
| Platt | Top 10% | 11,811 | 2,628 | 22.250% | 21.509–23.010% | 64.665% | 6.47x |

The constant-score prior has **no meaningful score-based top-k ranking**:
identical scores are broken by fixed input-row order, which can accidentally
favor an earlier part of the held-out time period. Never interpret the
constant-prior top-k precision/lift as predictive power. Native F03 and
ordinal F04 are different 100- and 150-estimator research studies, not one
direct tuning contest. No auto declines, real-dollar savings, calibrated
public API endpoint, model registry replacement or production model is
authorized.

## Current acceptance gates

| Gate | Decision | Remaining condition |
|---|---|---|
| Authorized Kaggle access and full training population | **PASS** | Source SHA verified; run original competition dataset |
| F03 temporal/feature hygiene experimental code and full-source evidence | **PASS — research** | Multi-fold robustness and independently reserved future data if candidate will be promoted |
| F04 60/20/20 empirical Platt/isotonic and top-k review-queue evidence | **PASS — research** | Calibrate a specifically versioned production-target base model and externally validate before publication |
| Deterministic ordered F03/F04 source fingerprint | **PASS** | Both independent runner fingerprints matched; model bitwise reproducibility across repeated fits was not separately certified |
| BigQuery authorized `fraud_project_reporting` row parity | **BLOCKED** | Fraud repo Actions WIF variables absent and provider/IAM repo trust incomplete; no live BigQuery API call performed |
| Full 27-dashboard report/parity and Vercel production SHA | **OPEN** | Reconcile derived views and public release separately; no snapshot refresh claimed |

BigQuery-specific blockers, the precise Fraud repository numeric ID and
repo-scoped WIF instructions are documented in
[BigQuery + Kaggle workplan](../archive/BIGQUERY_KAGGLE_WORKPLAN_2026-10-17.md)
and [issue #9](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/9).
Original unpublished Kaggle notebook recovery remains [issue #8](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/8);
production model calibration acceptance remains [issue #20](https://github.com/senanurcetin/ieee-fraud-detection-analytics/issues/20).
