"""Precompute the dashboard API payloads so the web app can serve them from disk.

The reporting marts only change when the pipeline is rebuilt, but the app used to
query BigQuery on every cache miss. A visitor arriving after an idle period paid
for a cold warehouse query, which took roughly 45 seconds. This script runs those
queries once and writes the responses next to the app.

Run it after `dbt build`, then commit the refreshed snapshots:

    python scripts/build_web_snapshot.py --credentials <service-account.json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEBAPP_DIR = ROOT / "webapp"
SNAPSHOT_DIR = WEBAPP_DIR / "snapshots"

# The case queue is sliced per request, so capture the largest supported page.
CASE_LIMIT = 500

TARGETS = {
    "dashboard": "/api/dashboard?refresh=true",
    "enterprise-segments": "/api/enterprise/segments?refresh=true",
    "enterprise-cases": f"/api/enterprise/cases?limit={CASE_LIMIT}",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default=os.environ.get("GCP_PROJECT_ID"))
    parser.add_argument("--dataset", default=os.environ.get("BQ_DATASET", "fraud_project_reporting"))
    parser.add_argument("--location", default=os.environ.get("BIGQUERY_LOCATION", "US"))
    parser.add_argument("--credentials", default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.project_id:
        raise SystemExit("Set GCP_PROJECT_ID or pass --project-id.")
    if not args.credentials or not Path(args.credentials).exists():
        raise SystemExit(f"Credential file not found: {args.credentials}")

    os.environ["GCP_PROJECT_ID"] = args.project_id
    os.environ["BQ_DATASET"] = args.dataset
    os.environ["BIGQUERY_LOCATION"] = args.location
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(Path(args.credentials).resolve())
    # Read through to BigQuery rather than to any snapshot already on disk.
    os.environ["WEB_SNAPSHOT_DISABLE"] = "1"

    sys.path.insert(0, str(WEBAPP_DIR))
    import main as webapp_main  # noqa: PLC0415
    from fastapi.testclient import TestClient  # noqa: PLC0415

    generated_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    client = TestClient(webapp_main.app)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in TARGETS.items():
        response = client.get(url)
        if response.status_code != 200:
            raise SystemExit(f"{url} returned {response.status_code}: {response.text[:300]}")
        payload = response.json()

        # Say plainly that this is precomputed, so the dashboard does not claim to
        # be reading BigQuery live.
        meta = payload.get("meta")
        if isinstance(meta, dict):
            meta["backend"] = "snapshot"
            meta["source_backend"] = "bigquery"
            meta["refreshed_at"] = generated_at

        path = SNAPSHOT_DIR / f"{name}.json"
        path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}: {path.stat().st_size / 1000:.0f} kB")

    print(f"\nSnapshot generated at {generated_at}. Commit webapp/snapshots/ and redeploy.")


if __name__ == "__main__":
    main()
