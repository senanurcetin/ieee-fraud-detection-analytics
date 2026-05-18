# BigQuery Free-Tier Deployment

This project is BigQuery-ready but does not assume credentials are present in the shell.

## Required Environment

```powershell
$env:GCP_PROJECT_ID="workintech-working"
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
$env:BIGQUERY_LOCATION="US"
```

## Load Raw Tables

```powershell
$PY="C:\Users\MONSTER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $PY src\upload_to_bigquery.py
```

The loader creates these datasets:

- `raw`
- `staging`
- `intermediate`
- `mart`
- `dbt_default`

Then run dbt against BigQuery:

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" run --project-dir dbt_ieee_fraud --profiles-dir profiles --profile ieee_fraud_detection --target prod
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" test --project-dir dbt_ieee_fraud --profiles-dir profiles --profile ieee_fraud_detection --target prod
```

## Free-Tier Guardrails

- Keep `maximum_bytes_billed` enabled in `profiles/profiles_bigquery.yml`.
- Query marts first; avoid scanning raw 400-column transaction tables in BI.
- Use clustered/partitioned marts only after the free-tier query pattern is understood.
- Do not upload Kaggle raw files to GitHub.
