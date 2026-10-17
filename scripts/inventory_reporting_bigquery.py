"""Read-only BigQuery table inventory for the IEEE-CIS reporting snapshot.

Uses BigQuery METADATA APIs only: get_dataset, list_tables and get_table.
Never executes SQL, downloads table rows, mutates cloud state or rewrites snapshots.
Project access must already be authorized. Do not share service-account files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.audit_reporting_snapshot import SNAPSHOT_PATH, SOURCES, read_json


def inventory(client: Any, project: str, dataset: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Collect table identity, schema and metadata only, without query jobs."""
    dataset_ref = f"{project}.{dataset}"
    meta = client.get_dataset(dataset_ref)
    present = {item.table_id for item in client.list_tables(dataset_ref)}
    expected = sorted(set(SOURCES.values()))
    declared_groups = len(SOURCES)
    details = {}
    for name in expected:
        if name not in present:
            details[name] = {"status": "MISSING"}
            continue
        info = client.get_table(f"{dataset_ref}.{name}")
        details[name] = {
            "status": "PRESENT",
            "table_type": getattr(info, "table_type", None),
            "row_count_metadata": getattr(info, "num_rows", None),
            "modified_metadata": (
                info.modified.isoformat() if getattr(info, "modified", None) else None
            ),
            "field_names": sorted(field.name for field in getattr(info, "schema", [])),
        }
    historical_meta = snapshot.get("meta", {})
    found = sum(item["status"] == "PRESENT" for item in details.values())
    location = getattr(meta, "location", None)
    identity_match = project == historical_meta.get("project_id") and dataset == historical_meta.get("dataset")
    return {
        "mode": "BIGQUERY_METADATA_ONLY",
        "status": (
            "MISSING_TABLES" if found != len(expected) else
            "IDENTITY_MISMATCH" if not identity_match or location != "US" else
            "INVENTORY_MATCH"
        ),
        "snapshot_project": historical_meta.get("project_id"),
        "snapshot_dataset": historical_meta.get("dataset"),
        "snapshot_refresh_unchanged": historical_meta.get("refreshed_at"),
        "source_project": project,
        "source_dataset": dataset,
        "source_location": location,
        "reporting_groups": declared_groups,
        "expected_unique_tables": len(expected),
        "present_expected_tables": found,
        "missing_expected_tables": sorted(set(expected) - present),
        "extra_source_tables": sorted(present - set(expected)),
        "tables": details,
        "sql_jobs_run": 0,
        "table_rows_downloaded": 0,
        "snapshot_rewritten": False,
        "source_content_parity_verified": False,
        "remark": (
            "24 table metadata entries correspond to 27 mapped presentation groups. "
            "Existence, schemas and row-count metadata cannot prove report value parity "
            "or make historical competition data current."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", required=True, type=Path)
    parser.add_argument("--project", default="workintech-working")
    parser.add_argument("--dataset", default="fraud_project_reporting")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.credentials_file.is_file():
        print("BigQuery inventory unavailable (credential file not found)", file=sys.stderr)
        return 2
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            str(args.credentials_file),
            scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
        )
        client = bigquery.Client(project=args.project, credentials=credentials)
        report = inventory(client, args.project, args.dataset, read_json(args.snapshot))
    except Exception as exc:
        # Do not echo exception messages; Google API errors can contain private identifiers.
        print(f"Read-only BigQuery inventory unavailable ({type(exc).__name__})", file=sys.stderr)
        return 2
    output = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)
    return 0 if report["status"] == "INVENTORY_MATCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
