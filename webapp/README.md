# NEXUS Fraud Analytics — Web Application

> **Historical research dashboard.** This FastAPI app serves committed IEEE-CIS reporting snapshots; the public visitor path does **not** query live BigQuery. Model scores are uncalibrated rankings. For dataset and release limitations see [documentation](../docs/README.md) and [release status](../docs/RELEASE_STATUS.md).

**Published site:** https://fraud-project-web.vercel.app

## UI structure

| Route | Content |
|---|---|
| `/` | Nine-page NEXUS analytics report, filter-linked visuals and threshold policy exploration |
| `/studio` | Historical Decision Studio with bounded, read-only case sample and keyboard-accessible review |
| `/api/dashboard` | Public committed reporting snapshot |
| `/api/evidence-status` | Source date, 24-table/27-group reference and explicit data/model limitations |
| `/api/metadata` | Analytical definitions and published reporting contract |
| `/api/enterprise/model-registry` | Model metadata and supporting research context |

### Nine report views

1. Executive Fraud Overview
2. Fraud Trend Analysis
3. Transaction Amount Analysis
4. Customer Risk Analysis
5. Masked Address & Distance Analysis
6. Behavioral Pattern Analysis
7. Feature Importance Analysis
8. Model Performance Analysis
9. Key Insights & Recommendations

Interactions include page navigation, relative-day and masked-segment slicers, chart/segment drill-through, threshold comparison, theme switch, safe CSV export and **browser print-to-PDF**. A printed page is not a separately validated server-generated PDF.

Global slicers do not necessarily recompute every upstream source mart; read visible denominators and report scopes before comparing cuts. Real personal identities, physical geography and transaction timestamps cannot be inferred from masked IEEE-CIS fields.

## Run the historical demo

From the repository root, using Python 3.11:

```bash
python -m pip install -r webapp/requirements.txt
python -m uvicorn webapp.main:app --host 127.0.0.1 --port 8000
python -m scripts.verify_snapshot_release --base-url http://127.0.0.1:8000
```

Run the final smoke command from a second terminal while the server is running. Open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/studio`.

Alternatively, use the root `docker compose build && docker compose up -d` flow and [Docker release runbook](../docs/F08_LOCAL_RELEASE.md). No cloud account is necessary for this mode.

## Snapshot, source and privacy contracts

The checked-in files under `webapp/snapshots/` are **historical**. They retain their actual source refresh date (**10 September 2026**) regardless of web request time. There are 27 report groups derived from 24 physical reporting-table names; their count difference is deliberate, not a missing-table claim.

- The UI cannot silently turn absent snapshots into public warehouse queries; missing data must fail visibly.
- Warehouse maintenance/refresh and sensitive transaction-detail routes require internal authorization and separate data-access reviews.
- Real local TreeSHAP instances are **not** included in public dashboard snapshots; unverified global importance must not be labeled personal case evidence.
- All reporting and model evidence is for research/review; the app does **not** trigger live fraud alerts, enforcement or account blocking.

For source revalidation see [read-only BigQuery checks](../docs/BIGQUERY_BOUNDED_SOURCE_PARITY.md) and [snapshot auditor](../docs/SNAPSHOT_PARITY_AUDIT.md). Do not regenerate snapshots or change `refreshed_at` without independently verifying authorized source data, integrity and cost.

## Validation and deployment

Run repository-level checks:

```bash
ruff check .
pytest
```

GitHub Actions also runs [real three-engine browser tests](../.github/workflows/browser-acceptance.yml) and [Docker/HTTP checks](../.github/workflows/container-smoke.yml). Both validate a local historical demonstration; they cannot prove an external Vercel alias matches the intended Git SHA.

Deploy only through the established, authorized Vercel release process, respecting Hobby quota and preview protection. Require [public commit/HTTP attestation](../docs/PUBLIC_RELEASE_ATTESTATION.md) for the actual production URL. **Do not** set broad cloud credentials merely to serve the committed historical demo, and never put access tokens in frontend code or issues.

The older [14 October 2026 readiness audit](../docs/archive/nexus_fraud_release_readiness_2026-10-14.md) is retained as an historical record, not a current production approval.
