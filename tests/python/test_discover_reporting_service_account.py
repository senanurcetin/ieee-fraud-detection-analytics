"""Credential-free tests for service-account BigQuery dataset inventory."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

MODULE = Path(__file__).resolve().parents[2] / "scripts" / "discover_reporting_service_account.py"
spec = importlib.util.spec_from_file_location("discover_reporting_service_account", MODULE)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_metadata_only_discovery_contract():
    datasets = [
        SimpleNamespace(dataset_id="fraud_project_reporting"),
        SimpleNamespace(dataset_id="fraud_project_raw"),
        SimpleNamespace(dataset_id="unrelated"),
    ]
    result = checker.summarize("workintech-working", datasets)
    assert result["project_id"] == "workintech-working"
    assert result["reporting_dataset_found"]
    assert result["fraud_datasets"] == ["fraud_project_raw", "fraud_project_reporting"]
    assert result["sql_queries"] == result["mutations"] == 0
    assert not result["data_freshness_verified"]


def test_dataset_absence_cannot_be_misread_as_freshness():
    report = checker.summarize("another-project", [])
    assert report["fraud_datasets"] == []
    assert not report["reporting_dataset_found"]
    assert not report["data_freshness_verified"]
