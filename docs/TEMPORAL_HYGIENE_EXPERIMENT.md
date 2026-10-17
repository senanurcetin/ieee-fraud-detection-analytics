# F03 — Temporal leakage hygiene research (experimental)

## What this changes

The published LightGBM output and static web dashboard remain unchanged. This
package adds a **separate, local read-only experiment** rather than silently
rewriting the audited September historical model or its metrics.

\`src/prepare_raw_and_ml.py\` currently assigns categorical integer codes from
**all labeled training rows** before splitting the last 20% by relative
\`TransactionDT\`. This may allow later categories to influence preprocessing
earlier in time. The pre-existing Vesta missingness selection also depends on
all training rows, including those used later for holdout. Finally, risk-band
quantiles are calculated using predictions over the combined development and
holdout rows. These are **temporal evaluation hygiene risks**; global category
vocabulary / missingness are *not* label/target leakage by themselves.

The experimental branch addresses all three without altering existing production
artifacts:

- \`chronological_holdout\` requires nonoverlapping elapsed times. Timestamp ties
  stay together, and invalid/degenerate timestamps are rejected.
- \`FoldPreprocessor.fit\` learns category codes on **development fit rows only**;
  missing and future-only categories become -1 on later rows. No vocabulary from
  the validation window or Kaggle test is incorporated.
- Every V1–V339 missingness decision is fit **only** on that fold's fit rows. The
  benchmark deliberately requests all available V columns *before* fold-local
  selection, even if the older production code dropped some globally.
- Expanding cross-validation windows are generated exclusively within the
  **development** portion (not using the final 20% holdout); each window receives
  a newly fitted encoder and V-feature selector.
- Risk-band score quantiles (p80 / p95 / p99) derive from **fit-window**
  predictions only. Validation results use those frozen fit-derived thresholds.
- Two experimental, otherwise identical LightGBM arms compare ordinal numeric
  codes against explicit native categorical handling. Both use the same
  chronology, feature policy, model parameters and binary labels.

## Run on an authorized local IEEE-CIS source

This study requires the *already prepared* local DuckDB \`raw.train_transaction\`
and \`raw.train_identity\` tables. It opens DuckDB \`read_only=True\` and **never**
downloads Kaggle data, accesses GCP, executes dbt builds, or replaces the
current model registry or dashboard snapshot.

~~~bash
python -m scripts.benchmark_temporal_hygiene \
  --duckdb data/processed/ieee_fraud.duckdb \
  --n-estimators 150 \
  --windows 3 \
  --min-train-rows 10000 \
  --output outputs/research/fraud_temporal_hygiene.json
~~~

For a **non-evidentiary subset smoke run**, supply \`--max-rows 20000\`.
Do not report a smoke subset result as the 590,540-transaction full-data result.
Larger estimator counts can be requested, but publish the exact settings.

The JSON records both arms' final holdout ROC-AUC, average precision,
fit-derived p95 review workload/precision/capture, selected V and categorical
feature counts, per-column unknown/missing codes, development fold metrics,
split sizes, a reproducible digest of identity/time/labels, and runtime versions.
It publishes **no raw transaction records, customer attributes or credentials**.

**Interpretation:** class-weighted LightGBM outputs ranking scores, not
empirically calibrated probabilities. A fit-derived p95 threshold does not
guarantee 5% workload on the later holdout because distribution can drift.
The original published benchmark (ROC-AUC 0.9134; AP 0.5354) uses different
preprocessing and 500 estimators, so this study is a diagnostic comparison
of *two equally strict experimental arms*, **not an apples-to-apples model
replacement claim**.

## Data-free CI tests

~~~bash
python -m pytest -q tests/python/test_temporal_hygiene.py
python -m ruff check src/temporal_hygiene.py \
  scripts/benchmark_temporal_hygiene.py tests/python/test_temporal_hygiene.py
~~~

Synthetic tests cover strict timestamps and ties, no reuse of final holdout
during CV, unknown future categories, fit-only V missingness, train-derived
risk quantiles, and both LightGBM fitting modes.

## Remaining work before promotion

1. Confirm the source dataset and reproduce the historical baseline on real
   Kaggle IEEE-CIS data with a source checksum.
2. Compare **identical** estimator counts and feature scopes for the historical
   and strict preprocessing (then ordinal versus native categorical) on the
   *same* chronological holdout and folds. This repository's original
   500-estimator model is not modified by the 150-estimator research tool.
3. Audit label balance and tie boundaries, fold fit preprocessing, score
   quality, operational p95 queue performance, model calibration, and time drift.
4. Only if repeatable evidence is better, version a new model and regenerate
   reports via separately authorized dbt / BigQuery source verification.
5. Continue separate calibrated-probability work in issue #20; raw ranking
   scores must not be promoted to automated credit/payment decisions.

Tracking: issue #8 (F03), issue #9 (F02), issue #20 (F04).
