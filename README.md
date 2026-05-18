# IEEE-CIS Fraud Detection Analytics Project

Professional EDA, dbt modeling, ML scoring, Power BI-ready marts, BigQuery-ready deployment assets, and presentation output for the Kaggle IEEE-CIS Fraud Detection dataset.

## Zero-Cost Execution Pattern

- Local warehouse: DuckDB file at `data/processed/ieee_fraud.duckdb`
- Transform: dbt Core with DuckDB adapter
- Cloud target: BigQuery free-tier compatible SQL/profile templates
- BI handoff: CSV marts under `outputs/powerbi/`
- Presentation: editable PowerPoint plus rendered preview PNGs under `outputs/presentation/`

Raw Kaggle files are intentionally ignored by git. Do not push Kaggle competition data to GitHub.

## Download Kaggle Data

If `C:\Users\MONSTER\Downloads\ieee-fraud-detection.zip` is not already present, use either script:

```powershell
.\scripts\download_kaggle.ps1
```

```bash
./scripts/download_kaggle.sh
```

## Run

```powershell
$PY="C:\Users\MONSTER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $PY src\prepare_raw_and_ml.py
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" run --project-dir dbt_ieee_fraud --profiles-dir profiles
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" test --project-dir dbt_ieee_fraud --profiles-dir profiles
& $PY src\export_powerbi_and_charts.py
& $PY src\create_powerbi_template.py
& $PY src\build_presentation_deck.py
```

Then open the generated Power BI template:

`outputs/powerbi/ieee_fraud_detection_dashboard.pbit`

The editable PowerPoint deck is generated at:

`outputs/presentation/ieee-cis-fraud-detection-analysis.pptx`

## BigQuery

The project includes BigQuery-ready loaders and dbt profile templates in `bigquery/` and `profiles/profiles_bigquery.yml`. A local service account JSON or Application Default Credentials is required before automated upload can run.
