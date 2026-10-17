# F04 — Temporal fraud risk score calibration (experimental)

> **Verified historical experiment, 17 October 2026:** A full 590,540-record Kaggle temporal 60/20/20 experiment has now run successfully on GitHub. See [source hashes, measured Brier/ECE/AP, reliability caveats and exact run](KAGGLE_TEMPORAL_CALIBRATION_EVIDENCE_2026-10-17.md). This evidence does **not** automatically calibrate the published 500-tree model or authorize production promotion.


This research is **stacked on F03** (\`feat/fraud-temporal-hygiene-20261017\`)
so that fold-fit preprocessing is available. It does **not** modify the
published model, report snapshots, website, API contract, or deployment.

## Temporal protocol

Keep every \`TransactionDT\` timestamp entirely on one side of each split:

1. **Core model fit:** roughly earliest 60% of historical IEEE-CIS rows.
   This is the *only* partition used to learn the LightGBM model, categorical
   code mapping, Vesta missingness filter and class-weight balance.
2. **Calibration window:** roughly next 20%, after the core training period.
   Platt/sigmoid logistic and isotonic calibrators learn from base model raw
   scores and **these labels only**. Their calibration maps cannot inspect
   any final-holdout labels.
3. **Untouched final holdout:** last roughly 20% used once for descriptive
   performance assessment. The constant fraud-prior baseline uses the
   **core training fraud rate**, not the later holdout prevalence.

Tie handling can make final row proportions differ slightly from 60/20/20.
A run is refused if a period has only one fraud class or time boundaries cannot
be made disjoint. This prevents apparent calibrated-probability quality built
using the same records both for fitting and evaluation.

The benchmark compares four predictions on exactly the same final holdout:

- Uncalibrated \`LightGBM\` class-weighted scores (ranking-only)
- Platt/sigmoid logistic calibration (fitted on the middle window)
- Isotonic regression calibration (fitted on the middle window)
- Constant fraud-rate baseline from the *core* training population

Metrics are ROC-AUC, average precision, Brier, log loss and ECE with fixed
ten-bin reliability tables. Isotonic may lose rank resolution via ties or
overfit a small number of calibration fraud positives. An apparently improved
Brier score does not itself imply a verified production fraud probability.

## Run from the repository root

Requires the already prepared, authorized IEEE-CIS DuckDB database.
Reads local source tables only and writes a **new local JSON report**.

~~~bash
python -m scripts.benchmark_temporal_calibration \
  --duckdb data/processed/ieee_fraud.duckdb \
  --n-estimators 150 \
  --output outputs/research/fraud_calibration.json
~~~

Optional: \`--native-categorical\` to fit LightGBM with true categorical
splitting, or \`--max-rows 10000\` for a **subset smoke run only**. No result
from a subset is evidence about the 590,540-row source. The report captures
row counts, time boundaries, method scores, reliability-bin counts, input
identity/time/label SHA256 fingerprint, versions and other reproducibility
metadata. It does not contain transaction-level records or service-account keys.

## CI tests

~~~bash
python -m pytest -q tests/python/test_temporal_hygiene.py \
  tests/python/test_temporal_calibration.py
python -m ruff check src/temporal_hygiene.py \
  scripts/benchmark_temporal_calibration.py tests/python/test_temporal_calibration.py
~~~

CI runs synthetic records only, with no Kaggle secrets, no GCP connections,
no BigQuery jobs, no dbt writes and no model promotion.

## Acceptance gates before considering a calibrated production artifact

- Reproduce the 500-estimator historical experiment on independently verified
  full Kaggle data; preserve source digest, code SHA and available feature set.
- Use the *same* model/feature scope, fit/core/calibration/final windows and
  consistent sampling for all calibration alternatives. This 150-estimator
  prototype is not comparable to the old 500-estimator dashboard metric.
- Verify calibration cohort support, bias by time and segment, proper Brier/ECE
  stability and uncertainty. Reserve independent unseen later data for final
  selection where possible.
- Approve any new versioned \`calibrated_fraud_probability\` contract separately
  from \`ranking_score\`. Do not relabel the current uncalibrated
  \`predicted_fraud_probability\` source as trustworthy.
- Do not use automated payment/credit decisions, make live-stream claims,
  update BI snapshots, or release a model based only on synthetic test success.

Issue #20 tracks scientific acceptance. This PR delivers experiment
infrastructure, not new full-data benchmark results.
