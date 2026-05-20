# GitHub Portfolio Checklist

## Repository Metadata

- Description: configured on GitHub.
- Topics: configured on GitHub.
- Homepage: configured on GitHub.
- License: MIT.
- Release tag: `v1.0.0`.

## Automation

- CI workflow: `.github/workflows/ci.yml`
- dbt docs workflow: `.github/workflows/dbt-docs.yml`
- Pre-commit: `.pre-commit-config.yaml`
- Python lint: Ruff
- Python tests: Pytest
- Dependency audit: pip-audit

## Documentation

- English-first root README.
- Architecture diagram.
- Data dictionary.
- Environment setup.
- Security and secrets guide.
- dbt project guide.
- Modeling decisions.
- Power BI report guide.

## Data Governance

- Raw Kaggle files are ignored.
- DuckDB files are ignored.
- Service-account files are ignored.
- Local dbt profile is ignored.
- Sanitized profile templates are committed.

## Report Assets

- Power BI file: `powerbi/fraud_project_v2.pbix`
- Supporting report assets: `powerbi/assets/`
- DAX measure layer: `powerbi/dax/fraud_project_measures.dax`
