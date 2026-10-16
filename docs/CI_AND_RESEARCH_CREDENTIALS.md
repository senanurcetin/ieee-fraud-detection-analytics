# CI and research credentials: explicit mode and cost gates

## Default CI

For push and pull requests, Ruff, offline unit tests, dependency audits and dbt parse run without downloading Kaggle IEEE-CIS records. A green default CI status is **not** evidence of a full-data ML experiment. The job summary explicitly reports "Full IEEE-CIS data build: NOT RUN".

## Intentional full-data execution

An authorized maintainer can provision a **fresh** Kaggle token as the GitHub Actions encrypted repository secret named KAGGLE_API_TOKEN (preferred), or keep the historical KAGGLE_USERNAME / KAGGLE_KEY pair. The CI workflow's manual **Run workflow** action is the only mode that may download Kaggle source rows and execute modeling and dbt run/test.

The Kaggle competition may still require acceptance of competition rules. Failures to authenticate or download are real failures; do not invent experiment results. Do not print or commit credentials. Delete temporary GitHub secrets after use, and revoke tokens with Kaggle; these are two separate operations.

## BigQuery and evidence policy

Never commit GCP service-account JSON. The source-inventory utility reads authorized local JSON and lists datasets only, without query charges. Dataset name matches do not verify row lineage or freshness. Obtain a dry-run estimate and explicit approval before billable BigQuery refreshes.

1. Require green CI checks before merge through repository rulesets/branch protection.
2. Distinguish metadata-only CI from full-data research evaluation.
3. Preserve dataset digest, seed, environment versions and actual metrics.
4. Mark external access blockers as BLOCKED, never PASS.
