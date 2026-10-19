# Environment Setup

## Runtime

Recommended versions:

- Python 3.11 or 3.12
- dbt Core compatible with `requirements.txt`
- FastAPI/Uvicorn compatible with `webapp/requirements.txt`
- Terraform 1.6+ for optional BigQuery dataset provisioning

## Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Kaggle Data

```bash
kaggle competitions download -c ieee-fraud-detection -p data/raw/kaggle_ieee_fraud
unzip -o data/raw/kaggle_ieee_fraud/ieee-fraud-detection.zip -d data/raw/kaggle_ieee_fraud
```

## dbt Profile

The committed dbt profile under `config/dbt/` is a sanitized template. It does not contain credential values and resolves local paths, project IDs, and service-account locations from environment variables.

Local target:

```bash
dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev
```

BigQuery target (optional; requires separately verified access and cost controls, not part of the $0 local demo):

```bash
export GCP_PROJECT_ID="your-gcp-project"
export BIGQUERY_LOCATION="US"
export GOOGLE_APPLICATION_CREDENTIALS="<private-service-account-json-path>"
dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target prod
```

## Validation

```bash
ruff check .
pytest
```

Use the pinned requirements in an isolated environment. On a shared Windows Python installation, unrelated globally installed Pytest plugins and a locked `pytest-current` directory can interfere with validation. The project tests require no external Pytest plugins; this PowerShell invocation uses a fresh temporary directory:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$qaTemp = Join-Path $env:TEMP ("fraud-qa-" + [guid]::NewGuid().ToString("N"))
python -m pytest --basetemp $qaTemp
```

This changes only test isolation. It does not provide Kaggle authentication, BigQuery access, source reconciliation or hosted deployment evidence. See [release status](RELEASE_STATUS.md).
