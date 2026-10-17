# Security Policy

## Scope

This is a research and portfolio analytics project built on the historical IEEE-CIS dataset. The FastAPI service exposes **historical, masked reporting snapshots**, not a public live-model inference API or a banking enforcement service. Nothing in this repository authorizes real customer scoring, automatic payment declines or account decisions.

## Credentials and private data

Never commit, upload to issues, place in screenshots, or write into CI logs:

- Google service-account JSON, private keys or `GOOGLE_APPLICATION_CREDENTIALS` content.
- Kaggle API tokens, `KAGGLE_USERNAME`/`KAGGLE_KEY` values, or OAuth bearer tokens.
- Raw Kaggle competition data, private feature stores, local DuckDB files or customer transaction records.
- `.env`, downloaded warehouse exports, private model explanations or secrets embedded in notebooks.

Use **least-privilege, expiring credentials**, private environment variables and approved secret stores. BigQuery source inspection should start with metadata and bounded read-only operations; do not run paid queries, mutate datasets or refresh public snapshots without separate authorization, dry-run cost review and source-quality checks.

If a service-account key was pasted into chat, committed or otherwise shared outside its authorized environment, **revoke or rotate that key** and audit its access; merely deleting a visible copy does not invalidate the secret.

## Continuous security checks

The standard [CI](.github/workflows/ci.yml) runs Ruff, Pytest, compilation, `pip-audit` for both `requirements.txt` and `requirements-dev.txt`, and dbt parse. The workflow **does not ignore a vulnerability advisory by default**. Do not add an audit exception without documenting the advisory, impact, owner and expiry.

The [Docker local demo](docs/F08_LOCAL_RELEASE.md) runs without root privileges or warehouse credentials. The [public release gate](docs/PUBLIC_RELEASE_ATTESTATION.md) checks exact commit identity and is designed to fail on missing/protected HTTPS evidence; never weaken production authentication just to make a test green.

## Reporting a vulnerability

Prefer GitHub **private vulnerability reporting / security advisory** for this repository if enabled; otherwise contact the maintainer through an established private channel. Avoid opening a public issue containing exploitable details or keys.

Include affected paths, reproducible steps, impact and mitigations, without including real credentials or customer data. Security findings must be reviewed before merging or publishing a new production build.
