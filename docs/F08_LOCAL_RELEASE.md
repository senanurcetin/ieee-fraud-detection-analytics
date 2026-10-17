# F08 — Zero-budget historical dashboard container

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
report contract and source integrity. It **does not necessarily build or boot
a Docker image** in CI. To claim an actual Docker runtime test, capture a
successful local `docker compose build/up` and run the smoke checker against
that exact image. Do not report a successful source-level pytest as a Docker
test.

## Future production publication

1. Independently confirm BigQuery 24-table/27-group parity and authorized
   source snapshot build. This is still issue #9.
2. Complete real-data F03/F04 scientific acceptance and local explanation
   artifact checks. They remain distinct from this historical web demo.
3. Obtain full browser verification (keyboard, responsive screens, exports,
   missing-data UI and no uncaught client exceptions).
4. Record intended git revision and test artifacts; verify model/registry,
   documentation and disclosure copy match that revision.
5. Check Vercel project permissions, remaining deployment quota and
   configured secrets. Trigger the existing **manual release** workflow
   only after explicit release authorization, then validate the deployment's
   actual immutable SHA, URL, HTTP responses and browser behavior.
6. Preserve Vercel preview protection and avoid billed quotas or unapproved
   service account use. No auto-push to production is configured by this PR.

## Deployment risk resolved

The prior FastAPI HTTP entrypoint directly imported
`src.local_shap`, which eagerly imported NumPy even when serving only
historical snapshots. The `webapp/requirements.txt` minimal runtime
does not install NumPy. F08 replaces this with
`webapp/explanation_store.py`, a pure-standard-library, read-only SQLite
reader. It preserves the existing private endpoint semantics without
requiring the ML training environment in Vercel or the offline Docker image.
