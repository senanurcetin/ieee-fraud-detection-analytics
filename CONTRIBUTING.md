# Contributing

This repository is structured as a production-style analytics project. Contributions should preserve reproducibility, data governance, and executive reporting quality.

## Development Workflow

1. Create a feature branch from the default branch.
2. Install runtime and development dependencies.
3. Copy `profiles/profiles.example.yml` to `profiles/profiles.yml`.
4. Run validation locally before opening a pull request.

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pre-commit install
ruff check .
pytest
python -m compileall webapp
```

If raw data is available locally:

```bash
python src/prepare_raw_and_ml.py
dbt build --project-dir . --profiles-dir profiles --profile ieee_fraud_detection --target dev
```

## Pull Request Checklist

- Code is formatted and linted with Ruff.
- Python tests pass.
- dbt models parse or build successfully for the intended target.
- Web dashboard contract tests pass if the reporting surface was changed.
- No raw Kaggle files, local DuckDB files, service-account files, or temporary outputs are committed.
- Documentation is updated when model, report, or deployment behavior changes.

## Data Handling

The Kaggle dataset is not redistributed in this repository. Contributors must download the data directly from Kaggle and comply with the competition terms.

## Commit Style

Prefer small commits with clear intent:

- `Add dbt reconciliation test`
- `Document BigQuery deployment requirements`
- `Refine web dashboard executive report layout`
