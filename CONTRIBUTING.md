# Contributing

Contributions should improve **reproducibility, source transparency, safety, and analytical quality**. This repository is a historical IEEE-CIS competition-data project, not a deployed real-time fraud decision engine.

## Before you open a pull request

1. Branch from `main` and keep the change scoped.
2. Use Python 3.11, a virtual environment, and the committed **`config/dbt/profiles.yml`** (there is no `profiles/profiles.example.yml` in this repo).
3. Work with the **committed historical snapshots** for UI changes. Do not fetch Kaggle or submit warehouse queries as a side effect of unit tests.
4. Update [the documentation index](docs/README.md) and relevant methodology/evidence files when you change contracts, outputs or behavior.
5. Run the applicable test gates.

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest
python -m compileall webapp
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
dbt deps --project-dir .
dbt parse --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev
```

Installing and running the optional pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

### Full data-dependent validation (opt-in)

The raw IEEE-CIS dataset is **not** shipped with this repo. When you have downloaded and accepted its Kaggle competition terms:

```bash
python src/prepare_raw_and_ml.py
dbt build --project-dir . --profiles-dir config/dbt --profile ieee_fraud_detection --target dev
```

The BigQuery `prod` profile, SQL jobs and report refreshes require **separate IAM authorization and billing safeguards**; a green GitHub PR CI normally runs dbt **parse**, not a full data build. Never represent a mocked or snapshot-only test as a fresh production query.

## Changes involving the public dashboard

The primary dashboard and historical Decision Studio are under `webapp/`. Preserve accessible controls, the nine report pages, honest source-age disclosures, and uncalibrated-score labeling. Public UI text is English-first.

For browser and container changes, check the separate [real-browser workflow](.github/workflows/browser-acceptance.yml) and [Docker/HTTP smoke workflow](.github/workflows/container-smoke.yml) after merging. Their outputs do **not** substitute for the [public Vercel release gate](.github/workflows/public-release-smoke.yml).

## Pull request checklist

- [ ] Clear purpose, scope, and a link to an issue if applicable.
- [ ] Ruff and Pytest pass; affected data/model behavior has focused regressions.
- [ ] dbt parse passes; full source-dependent tests are described as run or blocked.
- [ ] Documentation links, commands, release state and limitations are accurate.
- [ ] No API keys, service-account JSON, raw IEEE-CIS data, large exports or local DuckDB databases are committed.
- [ ] Model performance, score calibration and source freshness are supported by **the exact evaluation evidence cited**.
- [ ] Public release claims specify the exact reviewed Git SHA and verified target.

## Security

Report suspected secret exposure privately using [SECURITY.md](SECURITY.md). Do not place private credentials into PR bodies, issues, log files or screenshots. Commit messages should describe the change; prefer small, independently testable PRs.
