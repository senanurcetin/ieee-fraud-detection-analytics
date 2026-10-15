"""Unit tests for metadata-only BigQuery discovery without GCP credentials."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[2] / "scripts" / "discover_reporting_source.py"
spec = importlib.util.spec_from_file_location("discover_reporting_source", MODULE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fake_run(command):
    cmd = " ".join(command)
    if command[0] == "gcloud":
        return subprocess.CompletedProcess(command, 0, json.dumps([{"projectId": "fraud-project-123"}]), "")
    if "--project_id=fraud-project-123" in cmd:
        data = [
            {"datasetReference": {"datasetId": "fraud_project_staging"}},
            {"datasetReference": {"datasetId": "fraud_project_reporting"}},
            {"datasetReference": {"datasetId": "unrelated"}},
        ]
        return subprocess.CompletedProcess(command, 0, json.dumps(data), "")
    return subprocess.CompletedProcess(command, 1, "", "permission denied")


def test_finds_report_dataset_without_running_sql():
    projects = module.available_projects(fake_run)
    result = module.discover(projects, fake_run)
    assert result["reporting_candidates"] == ["fraud-project-123"]
    assert result["queries_executed"] == 0
    assert result["writes_executed"] == 0
    assert result["projects"][0]["fraud_datasets"] == [
        "fraud_project_reporting", "fraud_project_staging"
    ]


def test_missing_access_fails_closed_and_hides_stderr():
    result = module.discover(["another-project-123"], fake_run)
    assert not result["reporting_candidates"]
    assert "permission denied" not in json.dumps(result)
    assert result["projects"][0]["error"] == "Metadata command failed: bq (exit 1)"


def test_rejects_invalid_project_before_invoking_runner():
    def fail_if_called(_):
        raise AssertionError("Must not call shell")

    with pytest.raises(ValueError):
        module.discover(["$(dangerous command)"], fail_if_called)


def test_main_reports_absent_reporting_as_nonzero(capsys):
    ret = module.main(["--project", "another-project-123"], fake_run)
    assert ret == 1
    assert '"reporting_candidates": []' in capsys.readouterr().out
