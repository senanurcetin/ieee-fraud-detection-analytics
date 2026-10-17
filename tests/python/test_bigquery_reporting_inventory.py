"""Fake-client tests: reporting inventory never executes SQL or downloads rows."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
inventory_tool = importlib.import_module("scripts.inventory_reporting_bigquery")
parity = importlib.import_module("scripts.audit_reporting_snapshot")


class FakeMetadataClient:
    def __init__(self, present: set[str] | None = None, location: str = "US") -> None:
        self.present = present if present is not None else set(parity.SOURCES.values())
        self.location = location
        self.calls: list[tuple[str, str]] = []

    def get_dataset(self, dataset: str) -> SimpleNamespace:
        self.calls.append(("get_dataset", dataset))
        return SimpleNamespace(location=self.location)

    def list_tables(self, dataset: str) -> list[SimpleNamespace]:
        self.calls.append(("list_tables", dataset))
        return [SimpleNamespace(table_id=name) for name in sorted(self.present)]

    def get_table(self, name: str) -> SimpleNamespace:
        self.calls.append(("get_table", name))
        return SimpleNamespace(
            table_type="TABLE",
            num_rows=590540 if name.endswith("fact_train_transactions") else 1,
            modified=None,
            schema=[SimpleNamespace(name="transaction_count")],
        )


def snapshot_metadata() -> dict:
    return {
        "meta": {
            "project_id": "workintech-working",
            "dataset": "fraud_project_reporting",
            "refreshed_at": "2026-09-10T19:41:45Z",
        }
    }


def test_inventory_has_24_unique_references_and_does_not_fetch_rows() -> None:
    client = FakeMetadataClient()
    report = inventory_tool.inventory(
        client, "workintech-working", "fraud_project_reporting", snapshot_metadata()
    )
    assert report["status"] == "INVENTORY_MATCH"
    assert report["reporting_groups"] == 27
    assert report["expected_unique_tables"] == 24
    assert report["present_expected_tables"] == 24
    assert report["sql_jobs_run"] == 0
    assert report["table_rows_downloaded"] == 0
    assert report["snapshot_rewritten"] is False
    assert report["source_content_parity_verified"] is False
    assert len(client.calls) == 26
    assert {op for op, _ in client.calls} == {"get_dataset", "list_tables", "get_table"}


def test_missing_table_is_detected_without_query() -> None:
    expected = set(parity.SOURCES.values())
    missing = "rpt_segment_watchlist"
    client = FakeMetadataClient(present=expected - {missing})
    report = inventory_tool.inventory(
        client, "workintech-working", "fraud_project_reporting", snapshot_metadata()
    )
    assert report["status"] == "MISSING_TABLES"
    assert report["missing_expected_tables"] == [missing]
    assert report["tables"][missing]["status"] == "MISSING"
    assert not any(name.endswith(missing) for op, name in client.calls if op == "get_table")


@pytest.mark.parametrize(
    ("project", "location"),
    (("wrong-project", "US"), ("workintech-working", "EU")),
)
def test_project_or_region_conflicts_fail_inventory_gate(project: str, location: str) -> None:
    report = inventory_tool.inventory(
        FakeMetadataClient(location=location),
        project, "fraud_project_reporting", snapshot_metadata(),
    )
    assert report["status"] == "IDENTITY_MISMATCH"


def test_unmapped_extra_table_does_not_change_expected_count() -> None:
    client = FakeMetadataClient(present=set(parity.SOURCES.values()) | {"unused_reporting_table"})
    report = inventory_tool.inventory(
        client, "workintech-working", "fraud_project_reporting", snapshot_metadata()
    )
    assert report["status"] == "INVENTORY_MATCH"
    assert report["extra_source_tables"] == ["unused_reporting_table"]


def test_missing_credentials_exit_without_echoing_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    credential_file = tmp_path / "my-private-key.json"
    assert inventory_tool.main(["--credentials-file", str(credential_file)]) == 2
    output = capsys.readouterr().err
    assert "my-private-key" not in output
    assert "credential file not found" in output
