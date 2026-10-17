# F01 — Fraud production trust and release gates

Implemented on branch `fix/fraud-production-trust-gates-20261017`.

## What changed

- The five public API routes that accept `?refresh=true` now require a secret passed in the `X-Internal-Refresh-Token` header. The secret must match `WEB_INTERNAL_REFRESH_TOKEN` using constant-time comparison. Missing, incorrect, or unconfigured tokens return HTTP 403 *before* live reporting is built.
- Ordinary `GET /api/dashboard` remains public and serves the governed historical snapshot. If a required snapshot is missing in BigQuery mode, the public endpoint returns HTTP 503 rather than running an unbounded warehouse fallback. The token is not a query parameter and is never emitted in an API response.
- `scripts/build_web_snapshot.py` creates a process-local, short-lived token before importing FastAPI and supplies it to its internal `TestClient` requests. This preserves authorized offline snapshot generation without storing a persistent credential or passing one on the command line.
- Unsnapshotted `/api/enterprise/cases/{id}`, `/api/enterprise/cases/{id}/explain`, and `/api/diagnostics` require the same internal token for BigQuery reads. Public `/api/enterprise/cases` and `/api/enterprise/segments` use saved snapshots and fail with HTTP 503 if a required snapshot is absent.
- `.github/workflows/vercel-deploy.yml` is **manual-only** (`workflow_dispatch`) to avoid duplicate automatic deploys and free-tier quota use. If deployment secrets are missing, the run fails with a clear BLOCKED summary; it never reports a successful but skipped release.
- `.github/workflows/ci.yml` keeps normal PR/push data-free quality checks. A manually requested full-data run without Kaggle credentials now fails, rather than turning green while doing no full-data work.

## Operating guidance

Public dashboard: `GET /api/dashboard` reads the published historical snapshot. Source snapshot refresh must not be confused with ingestion of current payments.

Authorized maintenance: `python scripts/build_web_snapshot.py --project-id <authorized-project> --credentials <local-service-account-file>`. This creates a token inside the script, performs its authorized BigQuery queries, and writes local snapshot files. It does **not** bypass BigQuery billing permissions; review costs and data lineage before running.

Direct internal API usage: set `WEB_INTERNAL_REFRESH_TOKEN` to a strong server-only random string, then send `X-Internal-Refresh-Token: <value>` on the live refresh request. Never place the secret in a browser bundle, URL, GitHub commit, issue, or logs. Do not enable credential-bearing origins or expose this header to untrusted clients.

Publish: run the **Vercel Deploy** workflow manually after green CI and review; configure `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` via encrypted repository secrets. Verify the deployed commit and the resulting site rather than treating a CLI step alone as proof of public readiness.

## Known limitations for subsequent phases

- The internal-token check restricts the known public routes that can trigger BigQuery, but the backend still allows authorized query execution. Admin operations require budget, explicit runtime credential boundaries, quotas, and monitoring.
- The public case-detail and explanation endpoints now return 403 without internal authorization in BigQuery mode; this is an intentional security trade-off. A fully public case-explanation experience should use precomputed, appropriately governed artifacts or a separate authenticated service.
- Snapshot contents are historical; token authorization does not prove dataset parity or make the model ready for automated decisions. F02 remains open.

## Tests

`python -m pytest -q tests/python/test_fraud_release_gates.py tests/python/test_ci_credential_gates.py`

A green standard PR build is **not** a real-data model training run, a BigQuery `dbt run/test` run, or a successful production deployment.

## Release policy

This branch is for review and CI verification. No production deployment or source snapshot rewrite is implied by creating or testing the PR.
