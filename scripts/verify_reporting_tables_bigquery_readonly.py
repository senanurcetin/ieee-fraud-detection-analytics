"""Read-only, bounded BigQuery TABLEDATA parity against the committed fraud snapshot.

Uses get_dataset, list_tables, get_table and list_rows exclusively; zero SQL jobs.
No raw source data is written. Derived and filtered views are explicitly NOT
certified by direct table rows. Requires a separately authenticated environment.
"""
from __future__ import annotations

import argparse
import datetime
import decimal
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.audit_reporting_snapshot import (
    SNAPSHOT_PATH,
    SOURCE_SHAPE,
    SOURCES,
    compare_group,
    read_json,
)

DEFAULT_PROJECT = "workintech-working"
DEFAULT_DATASET = "fraud_project_reporting"
MAX_SOURCE_ROWS = 10_000


def normalized_value(value: Any) -> Any:
    """Convert date types for the existing snapshot auditor without lossy floats."""
    if value is None or isinstance(value, bool | int | float | str | decimal.Decimal):
        return value
    if isinstance(value, datetime.datetime | datetime.date | datetime.time):
        return value.isoformat()
    if isinstance(value, list | tuple):
        return [normalized_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalized_value(item) for key, item in value.items()}
    raise TypeError("Unsupported reporting field value")


def inspect(
    client: Any, snapshot: dict[str, Any], *,
    project: str = DEFAULT_PROJECT,
    dataset: str = DEFAULT_DATASET,
    max_source_rows: int = MAX_SOURCE_ROWS,
) -> dict[str, Any]:
    """Compare direct, bounded tables only; never infer full 27-group parity."""
    if not 1 <= max_source_rows <= MAX_SOURCE_ROWS:
        raise ValueError("Source read bound must be between 1 and 10000 rows")
    if not re.fullmatch(r"[a-z][a-z0-9-]{3,62}", project):
        raise ValueError("Invalid project")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]{0,1023}", dataset):
        raise ValueError("Invalid dataset")
    meta = snapshot.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("Historical snapshot metadata is missing")
    if project != meta.get("project_id") or dataset != meta.get("dataset"):
        raise ValueError("Target BigQuery source is not the committed snapshot source")
    dataset_ref = f"{project}.{dataset}"
    details = client.get_dataset(dataset_ref)
    region = getattr(details, "location", None)
    if region != "US":
        raise ValueError("Dataset region does not match recorded US source")
    physical = {entry.table_id for entry in client.list_tables(dataset_ref)}

    per_group: dict[str, dict[str, Any]] = {}
    for group, table in SOURCES.items():
        kind = SOURCE_SHAPE.get(group, "direct")
        historic = snapshot.get(group)
        result: dict[str, Any] = {
            "physical_table": table,
            "query_shape": kind,
            "source_rows_read": 0,
        }
        if not isinstance(historic, list) or not all(isinstance(x, dict) for x in historic):
            result["status"] = "INVALID_HISTORICAL"
        elif kind != "direct":
            result["status"] = "SKIPPED_DERIVED_OR_FILTERED"
        elif table not in physical:
            result["status"] = "MISSING_PHYSICAL_TABLE"
        else:
            try:
                info = client.get_table(f"{dataset_ref}.{table}")
                reported_count = getattr(info, "num_rows", None)
                if not isinstance(reported_count, int) or isinstance(reported_count, bool):
                    result["status"] = "UNBOUNDED_SOURCE"
                elif reported_count > max_source_rows:
                    result["status"] = "SOURCE_OVER_CAP"
                    result["source_row_count_metadata"] = reported_count
                else:
                    fields = {col.name for col in info.schema}
                    published_fields = {key for row in historic for key in row}
                    absent = sorted(published_fields - fields)
                    result["source_row_count_metadata"] = reported_count
                    if absent:
                        result["status"] = "MISSING_SOURCE_FIELDS"
                        result["missing_source_fields"] = absent
                    else:
                        # tabledata.list, not SQL; BigQuery client enforces max_results.
                        rows = list(client.list_rows(info, max_results=reported_count + 1))
                        result["source_rows_read"] = len(rows)
                        if len(rows) != reported_count:
                            result["status"] = "INCOMPLETE_SOURCE_READ"
                        else:
                            projected = [
                                {
                                    field: normalized_value(dict(row.items())[field])
                                    for field in published_fields
                                }
                                for row in rows
                            ]
                            verdict = compare_group(group, historic, projected)
                            result["comparison"] = verdict
                            if verdict["status"] == "MATCH":
                                result["status"] = (
                                    "MATCH_DIRECT_SCHEMA" if fields == published_fields
                                    else "MATCH_PUBLISHED_FIELDS"
                                )
                            else:
                                result["status"] = "DIFF_DIRECT"
                            result["source_extra_fields"] = sorted(fields - published_fields)
            except Exception:
                # Do not print API errors; they may contain tenant identifiers.
                result["status"] = "SOURCE_READ_ERROR"
        per_group[group] = result

    statuses = Counter(item["status"] for item in per_group.values())
    read_total = sum(item["source_rows_read"] for item in per_group.values())
    blockers = sorted(
        name for name, item in per_group.items()
        if item["status"] not in {
            "MATCH_DIRECT_SCHEMA",
            "MATCH_PUBLISHED_FIELDS",
            "SKIPPED_DERIVED_OR_FILTERED",
        }
    )
    return {
        "mode": "BOUNDED_BIGQUERY_TABLEDATA_READ_ONLY",
        "status": "DIRECT_TABLES_MATCH_PARTIAL_ONLY" if not blockers else "DIRECT_TABLES_UNRESOLVED",
        "project": project,
        "dataset": dataset,
        "region": region,
        "historical_refresh_unchanged": meta.get("refreshed_at"),
        "report_groups": len(SOURCES),
        "unique_source_table_references": len(set(SOURCES.values())),
        "source_row_limit_each": max_source_rows,
        "source_rows_read_total": read_total,
        "sql_query_jobs_submitted": 0,
        "raw_fraud_transactions_downloaded": False,
        "snapshot_rewritten": False,
        "verified_full_27_group_parity": False,
        "status_counts": dict(sorted(statuses.items())),
        "unresolved_direct_groups": blockers,
        "groups": per_group,
        "warning": (
            "Only bounded, directly table-backed published columns were compared. "
            "Derived aggregates, filtered views, source lineage, real-data model "
            "calibration and full 27-group snapshot parity remain UNVERIFIED. "
            "Metadata and tabledata API access may be subject to service quotas."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH)
    parser.add_argument("--max-source-rows", type=int, default=MAX_SOURCE_ROWS)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.credentials_file.is_file():
        print("Authorized service-account file not accessible", file=sys.stderr)
        return 2
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        auth = service_account.Credentials.from_service_account_file(
            str(args.credentials_file),
            scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
        )
        client = bigquery.Client(project=args.project, credentials=auth)
        result = inspect(
            client,
            read_json(args.snapshot),
            project=args.project,
            dataset=args.dataset,
            max_source_rows=args.max_source_rows,
        )
    except Exception:
        print("Read-only BigQuery parity inspection unavailable", file=sys.stderr)
        return 2
    report = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)
    return 0 if result["status"] == "DIRECT_TABLES_MATCH_PARTIAL_ONLY" else 1


if __name__ == "__main__":
    sys.exit(main())
