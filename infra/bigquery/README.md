# BigQuery Infrastructure

This Terraform module defines the BigQuery datasets used by `fraud_project`.

## Datasets

- `fraud_project_raw`
- `fraud_project_staging`
- `fraud_project_intermediate`
- `fraud_project_mart`
- `fraud_project_powerbi`

## Usage

```bash
cd infra/bigquery
terraform init
terraform plan -var="project_id=your-gcp-project" -var="location=US"
terraform apply -var="project_id=your-gcp-project" -var="location=US"
```

Authentication should be provided through the standard Google Cloud environment variables or an authenticated `gcloud` session. Do not place service-account JSON files in this repository.
