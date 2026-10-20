# Reproducible random vs chronological validation (new study)

> **17 Oct 2026 update:** The new study has now run successfully on the original, complete 590,540-row Kaggle IEEE-CIS competition dataset. See [measured results, exact Git run, SHA-256 and interpretation caveats](KAGGLE_FULL_SOURCE_VALIDATION_2026-10-17.md). The unavailable *original* Kaggle notebook remains unverified, and this new study uses different modeling settings.


The original Kaggle notebook *IEEE-CIS: How Much of Random-CV AUC Is Leakage?* is inaccessible (public HTTP 404) and its original notebook source has not been verified. This replacement is **new code**, and does not claim to reproduce its historical 0.971/0.921 scores.

## Data and methodology

Use the legitimate original IEEE-CIS competition `train_transaction.csv` after accepting the Kaggle competition rules. The analysis never commits or republishes CSV data. The study compares a stratified 80/20 random holdout with a chronological 80/20 holdout based on relative `TransactionDT`, using the same limited numeric predictor list and LightGBM settings. `TransactionDT`, `TransactionID` and `isFraud` are excluded from model predictors. Shared cutoff timestamps never cross the chronological split.

A **masked card-family feature proxy** (card1/card2/card3/card5/addr1) is used only to report whether a held-out card profile was previously seen; it is *not* a verified customer identity. Results report ROC-AUC, average precision and seen/unseen proxy subset metrics, with null for subsets that contain only one target class. A random–chronological score gap cannot by itself prove causal leakage because temporal drift and account correlation may also contribute.

## Run and verification

~~~
python scripts/compare_random_time_holdout.py --csv data/raw/kaggle_ieee_fraud/train_transaction.csv
python -m pytest tests/python/test_compare_random_time_holdout.py -q
~~~

The script writes a JSON result to `outputs/research/ieee_cis_split_comparison.json`, including source file SHA-256, environment package versions, split boundaries, predictors, sample sizes and measured metrics. `--max-rows` is a smoke-only subset, not full-data evidence.

A standalone Kaggle-ready notebook with the same analysis code is at [notebooks/ieee_cis_random_vs_time_reproduction.ipynb](../../notebooks/ieee_cis_random_vs_time_reproduction.ipynb). Upload the notebook to a Kaggle session with the IEEE-CIS dataset attached, then execute and publish it under the owner's account. **A full-data GitHub Actions run is now independently evidenced** by [17 October Kaggle study results](KAGGLE_FULL_SOURCE_VALIDATION_2026-10-17.md). The public Kaggle notebook URL remains **unverified** until the notebook is actually uploaded, executed and publicly accessible. Do not conflate GitHub-run metrics with a published Kaggle notebook or the missing original notebook's claims.

No Kaggle API tokens or BigQuery private keys are stored in this repository.
