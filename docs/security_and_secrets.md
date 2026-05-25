# Security and Secrets

## Secret Handling

The repository must not contain:

- Service-account JSON files
- Kaggle API tokens
- `.env` files
- Raw Kaggle CSV files
- DuckDB database files
- Temporary model outputs

Use environment variables instead:

```bash
export GCP_PROJECT_ID="your-gcp-project"
export BIGQUERY_LOCATION="US"
export GOOGLE_APPLICATION_CREDENTIALS="<private-service-account-json-path>"
export KAGGLE_USERNAME="your-kaggle-username"
export KAGGLE_KEY="your-kaggle-api-key"
```

## GitHub Actions Secrets

Recommended repository secrets:

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `GCP_PROJECT_ID`
- `BIGQUERY_LOCATION`
- `GCP_SERVICE_ACCOUNT_JSON`

## Local Profile Policy

`config/dbt/profiles.yml` is committed as a sanitized template only. It must not be edited with machine-specific secrets or absolute credential paths. Use environment variables or a private dbt profile directory outside the repository for local overrides.

Keep machine-specific paths outside committed files.

## BigQuery IAM

Minimum roles:

- BigQuery Job User
- BigQuery Data Editor
- BigQuery Data Viewer

Use least-privilege service accounts. Rotate keys if a credential path or key content is exposed.
