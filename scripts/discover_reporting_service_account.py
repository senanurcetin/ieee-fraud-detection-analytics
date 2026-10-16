"""Discover fraud datasets with a Google Cloud service-account JSON (read-only).

Does not execute SQL, refresh reports, write to BigQuery or print credential data.
Requires google-cloud-bigquery, already declared in project dependencies.

Run on a network-enabled trusted machine:
    python scripts/discover_reporting_service_account.py --credentials-file /safe/path/key.json

An explicit --project can inspect another GCP project only if the account has IAM
permission. Project ID in the JSON is NOT proof that the fraud dataset lives there.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

PREFIX = "fraud_project_"
EXPECTED = ("fraud_project_raw", "fraud_project_staging", "fraud_project_reporting")


def summarize(project: str, datasets: Iterable[Any]) -> dict[str, Any]:
    names = sorted({
        str(item.dataset_id)
        for item in datasets
        if isinstance(getattr(item, "dataset_id", None), str) and item.dataset_id.startswith(PREFIX)
    })
    return {
        "project_id": project,
        "fraud_datasets": names,
        "missing_expected": sorted(set(EXPECTED) - set(names)),
        "reporting_dataset_found": "fraud_project_reporting" in names,
        "sql_queries": 0,
        "mutations": 0,
        "data_freshness_verified": False,
        "remark": "Dataset metadata alone cannot establish intended data lineage or snapshot freshness.",
    }


def discover(credentials_file: Path, project: str | None = None) -> dict[str, Any]:
    if not credentials_file.is_file():
        raise FileNotFoundError("Credentials file not found")
    # Import inside discover so summarize can be unit tested without network packages.
    from google.cloud import bigquery
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_file), scopes=["https://www.googleapis.com/auth/bigquery.readonly"]
    )
    target_project = project or credentials.project_id
    if not target_project:
        raise ValueError("Service account does not specify a project; supply --project")
    # list_datasets calls BigQuery dataset metadata APIs; it does NOT execute
    # the query engine, read table records, or create billing jobs.
    client = bigquery.Client(credentials=credentials, project=target_project)
    return summarize(target_project, client.list_datasets(project=target_project))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--project", default=None, help="Optional target project with granted IAM read access")
    args = parser.parse_args(argv)
    try:
        report = discover(args.credentials_file, args.project)
    except Exception as exc:
        # Never print the exception message: transport errors might contain URLs
        # or sensitive environment values. Do not echo key contents or file path.
        print(f"Read-only BigQuery metadata discovery failed ({type(exc).__name__})", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["reporting_dataset_found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
