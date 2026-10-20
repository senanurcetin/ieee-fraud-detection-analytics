# CI and research credentials: explicit mode and cost gates

## Default CI

For push and pull requests, Ruff, offline unit tests, dependency audits and dbt parse run without downloading Kaggle IEEE-CIS records. A green default CI status is **not** evidence of a full-data ML experiment. The job summary explicitly reports "Full IEEE-CIS data build: NOT RUN".

## Intentional full-data execution

An authorized maintainer can provision a **fresh** Kaggle token as the GitHub Actions encrypted repository secret named KAGGLE_API_TOKEN (preferred), or keep the historical KAGGLE_USERNAME / KAGGLE_KEY pair. The CI workflow's manual **Run workflow** action is the only mode that may download Kaggle source rows and execute modeling and dbt run/test.

For **research-only** execution without the 500-estimator default modeling/dbt build, use the [manual Kaggle Research Evidence workflow](KAGGLE_RESEARCH_RUNBOOK.md). Its `access_check`, `random_vs_time`, `temporal_hygiene`, and `calibration` choices upload only safe aggregated metrics and source hashes, never original CSVs. It cannot run on a push/PR; manual `workflow_dispatch` is required.

The Kaggle competition may still require acceptance of competition rules. Failures to authenticate or download are real failures; do not invent experiment results. Do not print or commit credentials. Delete temporary GitHub secrets after use, and revoke tokens with Kaggle; these are two separate operations.

## BigQuery and evidence policy

Never commit GCP service-account JSON. The [keyless, manual GitHub WIF parity workflow](../archive/BIGQUERY_KAGGLE_WORKPLAN_2026-10-17.md) uses temporary OIDC-based ADC and read-only BigQuery metadata/bounded tabledata APIs, provided this Fraud repo has its own properly authorized IAM binding and repository variables. The local source-inventory utility can still read explicitly authorized local JSON. Neither method executes SQL query jobs; API requests may consume quotas. Dataset name matches do not verify row lineage or freshness. Obtain a dry-run estimate and explicit approval before billable BigQuery refreshes.

1. Require green CI checks before merge through repository rulesets/branch protection.
2. Distinguish metadata-only CI from full-data research evaluation.
3. Preserve dataset digest, seed, environment versions and actual metrics.
4. Mark external access blockers as BLOCKED, never PASS.
