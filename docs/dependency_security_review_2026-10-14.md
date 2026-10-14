# Runtime and CI dependency security check — 14 October 2026

## Scope / executable evidence

This is a dated dependency-advisory audit, **not** a complete security certification or an endorsement of every executable dependency, external script, or data flow.

- `python -m pip_audit -r requirements.txt --progress-spinner off` — **no known vulnerabilities found** in Fraud Analytics runtime requirements as resolved in the local Python 3.11 environment.
- Prior `python -m pip_audit -r requirements-dev.txt --progress-spinner off` — **failed**: two findings from the same `PYSEC-2026-1845` advisory against `pytest==8.3.4`, both carrying `9.0.3` as an upstream fixed version.
- **Remediation:** pin `pytest==9.1.1` in `requirements-dev.txt` (installed in the verifying environment; no known advisories reported by `pip-audit --disable-pip --no-deps -r requirements-dev.txt`). This direct pin scan does not resolve/check all possible transitive dev dependencies; the previous full scan isolated pytest as the affected package.
- Regression: `python -m pytest -q` with `pytest 9.1.1` — **36/36 passed**, exit code 0; only third-party `pkg_resources` deprecation warnings.
- CI prevention: the existing GitHub Actions dependency-audit step now checks **both** `requirements.txt` and `requirements-dev.txt`. Hosted GitHub Actions rerun was not triggered here to conserve remaining runner quota; do not claim hosted CI green on this correction.

## Responsible claims and remaining security scope

A clean known-CVE result does not replace SAST, secret scanning, authorization review, supply-chain integrity, dependency hash locking, browser accessibility tests, or production penetration testing. This change does not modify the model, BigQuery reporting source, dashboard API, dataset, or risk metrics.

The production dashboard uses governed IEEE-CIS *historical* snapshot evidence; source revalidation and the non-live data boundary are documented separately in [BigQuery read-only revalidation](bigquery_source_revalidation_2026-10-14.md).
