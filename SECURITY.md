# Security Policy

## Secrets

Do not commit credentials, service-account JSON files, Kaggle tokens, local `.env` files, DuckDB files, or raw Kaggle data.

Required secrets should be provided through environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`
- `GCP_PROJECT_ID`
- `BIGQUERY_LOCATION`
- `KAGGLE_USERNAME`
- `KAGGLE_KEY`

GitHub Actions should store sensitive values in GitHub Secrets.

## Dependency Audit

CI runs `pip-audit` against `requirements.txt`. The current workflow ignores `PYSEC-2024-277` because the advisory is reported for the resolved `joblib` dependency without a fixed version in the audit feed. This exception should be removed when an upstream fix is available.

## Supported Use

This project is an analytics portfolio implementation. It does not expose a public inference API and should not be used as an automated fraud decision system without model governance, bias review, production monitoring, and business approval.

## Reporting Issues

Open a private security advisory or contact the repository owner if you identify credential exposure, unsafe data handling, or report artifacts containing sensitive values.
