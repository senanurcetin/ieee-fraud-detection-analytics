"""Read-only discovery of BigQuery projects holding IEEE-CIS fraud dbt datasets.

Only gcloud projects list and bq ls metadata operations are used. The program
does not execute SQL, generate billing, refresh the snapshot or log keys.
Run locally with authenticated gcloud/bq CLI:
    python scripts/discover_reporting_source.py
or restrict scope:
    python scripts/discover_reporting_source.py --project PROJECT_ID
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from typing import Any

Run = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
DATASET_PREFIX = "fraud_project_"
EXPECTED_DATASETS = ("fraud_project_raw", "fraud_project_staging", "fraud_project_reporting")
ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command), capture_output=True, text=True, check=False, timeout=40
    )


def _json_result(command: Sequence[str], runner: Run) -> list[dict[str, Any]]:
    try:
        result = runner(command)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Metadata command unavailable: {command[0]} ({type(exc).__name__})") from exc
    if result.returncode != 0:
        # Do not echo stderr: it can contain user-supplied environment details.
        raise RuntimeError(f"Metadata command failed: {command[0]} (exit {result.returncode})")
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Metadata output was not JSON: {command[0]}") from exc
    if not isinstance(parsed, list):
        raise RuntimeError(f"Metadata command returned a non-list: {command[0]}")
    return [item for item in parsed if isinstance(item, dict)]


def available_projects(runner: Run = _run) -> list[str]:
    records = _json_result(("gcloud", "projects", "list", "--format=json"), runner)
    project_ids = [p.get("projectId") for p in records]
    return sorted({p for p in project_ids if isinstance(p, str) and ID_PATTERN.fullmatch(p)})


def discover(project_ids: Sequence[str], runner: Run = _run) -> dict[str, Any]:
    """Inspect dataset names only, never query tables or change cloud state."""
    records: list[dict[str, Any]] = []
    for project in sorted(set(project_ids)):
        if not ID_PATTERN.fullmatch(project):
            raise ValueError(f"Invalid GCP project identifier: {project!r}")
        cmd = ("bq", "ls", "--format=prettyjson", f"--project_id={project}")
        try:
            listing = _json_result(cmd, runner)
            datasets = sorted({
                ds_id["datasetId"]
                for item in listing
                if isinstance((ds_id := item.get("datasetReference")), dict)
                and isinstance(ds_id.get("datasetId"), str)
                and ds_id["datasetId"].startswith(DATASET_PREFIX)
            })
            row = {
                "project_id": project,
                "fraud_datasets": datasets,
                "missing_expected": sorted(set(EXPECTED_DATASETS) - set(datasets)),
                "contains_reporting": "fraud_project_reporting" in datasets,
            }
        except RuntimeError as exc:
            row = {"project_id": project, "error": str(exc)}
        records.append(row)
    return {
        "mode": "READ_ONLY_DATASET_METADATA",
        "queries_executed": 0,
        "writes_executed": 0,
        "projects": records,
        "reporting_candidates": [r["project_id"] for r in records if r.get("contains_reporting")],
        "next_step": (
            "Confirm project authorization, dataset region and source lineage; estimate query "
            "bytes with a dry run before any paid query or snapshot refresh."
        ),
    }


def main(argv: Sequence[str] | None = None, runner: Run = _run) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", action="append", default=[], help="Known GCP project ID (repeatable)")
    args = parser.parse_args(argv)
    try:
        projects = args.project or available_projects(runner)
        report = discover(projects, runner)
    except (RuntimeError, ValueError) as exc:
        print(f"Discovery blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["reporting_candidates"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
