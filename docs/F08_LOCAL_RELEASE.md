# F08 — Zero-budget historical dashboard container

> Current scope: full-source F03/F04 research has measured canonical results; model promotion and BigQuery parity remain separate. The 19 October release passed exact-SHA/HTTPS and container checks. Playwright is disabled at the owner's request. Use [release status](RELEASE_STATUS.md) for the current gates.

This is a **local portfolio demo**, not production authorization for payment
decisions or live bank traffic. It uses only the committed September 10, 2026
IEEE-CIS / BigQuery reporting snapshot, and never requires Kaggle credentials,
GCP billing, model training, a Vercel quota, or customer records.

## Run locally

Requires a local Docker Engine with Compose support.

```sh
docker compose build
docker compose up -d
python -m scripts.verify_snapshot_release --base-url http://127.0.0.1:8000
```

Visit [the local NEXUS fraud dashboard](http://127.0.0.1:8000/) and its
`/api/evidence-status`. A correctly presented historical snapshot produces
`PASS_HISTORICAL_OFFLINE_DEMO`; the report explicitly sets all
`live_data_verified`, `production_deployed`, `bigquery_parity_verified`
and `model_promoted` flags to **false**. This is a local smoke check only.

Stop the demo without uploading logs or data:

```sh
docker compose down
```

The image is built from the **webapp directory only**. The allowlist
`.dockerignore` excludes raw data, model directories, local notebooks,
credentials and external source files from the build context. No expensive
model/scikit-learn/NumPy/SHAP packages are required for the snapshot HTTP
server. The private instance-attribution reader is standard-library only.

Security defaults:

- Rootless container user `nexus`.
- Port 8000 is bound **only to 127.0.0.1** on the host.
- Read-only root filesystem with a small temporary filesystem.
- All Linux capabilities dropped; `no-new-privileges` applied.
- Memory and process limits for a lightweight demo.
- Private warehouse/API refresh token is **not** supplied by default.
- Docker health probe reads **only** the safe public snapshot evidence API;
  it never probes BigQuery, payment providers or cloud metadata services.

The container may still need to fetch the upstream Python base image and
pinned Python packages at build time. These network fetches are distinct from
live reporting or paid data queries.

## SHAP evidence and static demo

The local offline model pipeline may optionally write
`outputs/tables/local_shap_explanations.sqlite` during an authorized
full IEEE-CIS training run. That artifact is **not included** in this
container and is not publicly mounted. The real TreeSHAP API cannot return
case attributions until a separately authorized deployment config points
to a valid, privately mounted artifact and supplies internal auth.

The legacy global-importance visualizations remain disclosed as heuristics,
never genuine individual TreeSHAP. The uncalibrated ranking scores are not
certified fraud probabilities.

## Verification and limitations

```sh
pytest -q tests/python/test_f08_local_release.py tests/python/test_f08_release_smoke.py
ruff check webapp/main.py webapp/explanation_store.py scripts/verify_snapshot_release.py
```

The normal GitHub workflow validates Python semantics, privacy boundaries,
report contract and source integrity. The separate **Historical Container Smoke** workflow builds and boots the Docker image; ordinary Python CI alone does not. To claim an actual Docker runtime test, capture a
successful local `docker compose build/up` and run the smoke checker against
that exact image. Do not report a successful source-level pytest as a Docker
test.

## Hosted publication and remaining scope

1. The dated BigQuery 24-source/27-group reconciliation and separate full-source calibration research are complete. See [completed evidence](research/COMPLETED_VALIDATION_2026-10-21.md). Retain the historical snapshot unless new source evidence supports a change.
2. Current native Chromium desktop/mobile checks passed; the broader keyboard, export, error and browser-matrix acceptance remains tracked in issue #29.
3. For each later implementation release, record the intended Git revision, model/registry contracts and actual verification results separately.
4. Check project permissions and available free-tier quota before a new deployment. The existing Vercel Git integration publishes reviewed changes; use the optional manual deployment workflow only when needed, avoiding duplicate deploys.
5. Verify the actual deployed SHA and public HTTP behavior independently. [Release status](RELEASE_STATUS.md) links the measured implementation release, Docker and HTTPS results.
