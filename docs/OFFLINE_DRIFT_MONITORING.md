# F06 — Offline score distribution and missingness monitoring (first slice)

The first MLOps monitoring package compares **two explicitly supplied,
strictly time-ordered historical IEEE-CIS cohorts**. It does not poll live
payments, re-train models, inspect future labels, send alerts to customers
or claim real-time fraud performance.

The current LightGBM model is a **ranker**, and the file column
\`predicted_fraud_probability\` is an uncalibrated ranking score despite its
legacy name. This analysis does not convert that score into a validated
probability; calibrated-probability acceptance remains in F04.

## Operator flow

Prepare two scored CSV files with a score and \`TransactionDT\` column from
an **authorized local environment**, ensuring every reference time is earlier
than every observation time. Optional Vesta or other feature fields can be
included solely for missingness checks.

~~~bash
python -m scripts.audit_offline_drift \
  --reference /private/ieee_cis_earlier_scored.csv \
  --observed /private/ieee_cis_later_scored.csv \
  --score-column predicted_fraud_probability \
  --time-column TransactionDT \
  --feature V9 \
  --feature V22 \
  --output outputs/research/fraud_offline_drift.json
~~~

The script reads **only explicitly allowed score/time/feature columns**, never
fraud labels; reports real input-file SHA-256 digests but not source paths or
transaction values. It does not call BigQuery, download Kaggle data, modify
the model registry or rewrite the published static snapshot. The report is
written locally to Git-ignored \`outputs/research\`; review before public sharing.

## Evidence in each report

- Distinct earlier/later cohort row counts and strict elapsed-time boundaries.
  \`TransactionDT\` is elapsed time, **not** an actual calendar timestamp.
- Fixed, predeclared ranking-score bins across \`[0,1]\`; PSI (population
  stability index) with **0.5 pseudocount per bin** for finite empty-bin
  comparisons, plus per-bin contributions.
- Shift in mean and 95th percentile of ranking scores.
- Per-feature missingness fractions, change magnitude and explicit
  \`SCHEMA_MISSING\` if an expected feature is absent.
- Reproducible thresholds, full input file SHA-256 digests and the fact that
  no labels or online payment data were analyzed.

Default thresholds are investigation PSI >= 0.25, review PSI >= 0.10, and
an absolute missingness change >= 0.05. At least 200 rows per cohort are
required for a normal status; smaller windows return
\`INSUFFICIENT_SUPPORT\`. Thresholds are **screening heuristics**, not
universally validated fraud model release standards.

## Return statuses

- \`NO_POLICY_FLAG\` (exit 0): no drift flags under current policy, **not**
  proof of model performance or lack of fraud.
- \`REVIEW_SHIFT\` (exit 1): moderate score PSI / missingness shift.
- \`INVESTIGATE_SHIFT\` (exit 1): material score PSI shift.
- \`SCHEMA_REVIEW_REQUIRED\` (exit 1): expected feature missing from source.
- \`INSUFFICIENT_SUPPORT\` (exit 1): cohorts too small for ordinary signals.
- Invalid/overlapping timestamps, malformed scores, missing files, label
  feature requests: exit 2 and a generic error that omits local paths.

**Do not automatically retrain or promote a model, block payments, or claim
fraud concept drift on the basis of PSI alone.** Statistical drift can be
benign and model deterioration requires independently verified later labels
and task-performance evidence. This package measures distributions only.

## Offline CI

~~~bash
pytest -q tests/python/test_offline_drift_monitoring.py
ruff check src/drift_monitoring.py scripts/audit_offline_drift.py \
  tests/python/test_offline_drift_monitoring.py
~~~

All tests use synthetic data without authentication, Kaggle download,
BigQuery SQL, outbound networking or live transactions.

## Remaining F06 work

1. Verify actual full-data scored cohorts and their strict temporal lineage.
2. Store approved baseline score-bin distributions, model/environment SHA
   and source dataset version; identify snapshot/version mismatches.
3. Add periodic **opt-in, budget-gated** batch scoring and alert delivery
   after a real deployment endpoint/source is verified.
4. Add labeled performance drift (ROC-AUC, AP, Brier/ECE, precision at
   reviewed capacity) only when matured downstream labels are available.
5. Version monitoring checks with model registry and runbook, plus
   access/retention controls before operational release.
