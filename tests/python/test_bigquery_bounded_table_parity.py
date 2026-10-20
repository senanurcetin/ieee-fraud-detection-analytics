"""Synthetic safety and parity tests; no credentials, SQL or outbound traffic."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
audit = importlib.import_module("scripts.audit_reporting_snapshot")
verify = importlib.import_module("scripts.verify_reporting_tables_bigquery_readonly")


class FakeClient:
    def __init__(self, *, changed: str | None = None, extra_fields: bool = False):
        self.changed = changed
        self.extra_fields = extra_fields
        self.rows_requested: list[tuple[str, int]] = []
        self.tables_read: list[str] = []
        self.overcap: str | None = None
        self.location = "US"

    def get_dataset(self, dataset_ref: str):
        assert dataset_ref == "workintech-working.fraud_project_reporting"
        return SimpleNamespace(location=self.location)

    def list_tables(self, dataset_ref: str):
        assert dataset_ref == "workintech-working.fraud_project_reporting"
        return [SimpleNamespace(table_id=table) for table in sorted(set(audit.SOURCES.values()))]

    def get_table(self, table_ref: str):
        name = table_ref.rsplit(".", 1)[-1]
        assert name != "fact_train_transactions"
        self.tables_read.append(name)
        return SimpleNamespace(
            name=name,
            schema=[SimpleNamespace(name="sample")] + (
                [SimpleNamespace(name="extra")] if self.extra_fields else []
            ),
            num_rows=20_000 if name == self.overcap else 1,
        )

    def list_rows(self, info, *, max_results: int):
        self.rows_requested.append((info.name, max_results))
        assert max_results == 2
        value = 2 if info.name == self.changed else 1
        return [{"sample": value, **({"extra": "private"} if self.extra_fields else {})}]


def historical():
    return {
        "meta": {
            "project_id": "workintech-working",
            "dataset": "fraud_project_reporting",
            "refreshed_at": "2026-09-10T19:41:45Z",
        },
        **{name: [{"sample": 1}] for name in audit.SOURCES},
    }


def test_verified_direct_tables_are_never_confused_with_full_snapshot_parity() -> None:
    client = FakeClient()
    result = verify.inspect(client, historical())
    assert result["status"] == "DIRECT_TABLES_MATCH_PARTIAL_ONLY"
    assert result["verified_full_27_group_parity"] is False
    assert result["sql_query_jobs_submitted"] == 0
    assert result["snapshot_rewritten"] is False
    assert result["raw_fraud_transactions_downloaded"] is False
    assert result["report_groups"] == 27
    assert result["unique_source_table_references"] == 24
    assert result["status_counts"]["SKIPPED_DERIVED_OR_FILTERED"] == 7
    assert result["status_counts"]["MATCH_DIRECT_SCHEMA"] == 20
    assert all(limit == 2 for _, limit in client.rows_requested)
    assert "fact_train_transactions" not in client.tables_read


def test_source_field_change_revealed_without_dumping_records() -> None:
    client = FakeClient(changed="rpt_executive_kpis")
    result = verify.inspect(client, historical())
    assert result["status"] == "DIRECT_TABLES_UNRESOLVED"
    assert "executive_kpis" in result["unresolved_direct_groups"]
    assert result["groups"]["executive_kpis"]["status"] == "DIFF_DIRECT"
    assert "private" not in str(result)


def test_schema_projection_cannot_be_presented_as_full_row_schema_match() -> None:
    result = verify.inspect(FakeClient(extra_fields=True), historical())
    assert result["status_counts"]["MATCH_PUBLISHED_FIELDS"] == 20
    assert result["verified_full_27_group_parity"] is False
    assert result["groups"]["executive_kpis"]["source_extra_fields"] == ["extra"]


def test_table_over_cap_is_never_read() -> None:
    client = FakeClient()
    client.overcap = "rpt_executive_kpis"
    result = verify.inspect(client, historical(), max_source_rows=100)
    assert result["groups"]["executive_kpis"]["status"] == "SOURCE_OVER_CAP"
    assert ("rpt_executive_kpis", 2) not in client.rows_requested
    assert result["status"] == "DIRECT_TABLES_UNRESOLVED"


@pytest.mark.parametrize("max_rows", [0, -1, 10_001])
def test_invalid_read_limit_fails_before_network(max_rows):
    with pytest.raises(ValueError):
        verify.inspect(FakeClient(), historical(), max_source_rows=max_rows)


def test_mismatched_project_and_region_fail_closed_before_comparison() -> None:
    client = FakeClient()
    with pytest.raises(ValueError):
        verify.inspect(client, historical(), project="wrong-project")
    assert not client.tables_read
    client.location = "EU"
    with pytest.raises(ValueError):
        verify.inspect(client, historical())
    assert not client.tables_read


def test_unsupported_source_field_types_fail_for_group_not_entire_process() -> None:
    class BadRowsClient(FakeClient):
        def list_rows(self, info, *, max_results: int):
            if info.name == "rpt_executive_kpis":
                return [{"sample": object()}]
            return super().list_rows(info, max_results=max_results)

    result = verify.inspect(BadRowsClient(), historical())
    assert result["groups"]["executive_kpis"]["status"] == "SOURCE_READ_ERROR"
    assert result["status"] == "DIRECT_TABLES_UNRESOLVED"


def test_presentation_copy_explains_text_without_masking_numeric_changes() -> None:
    from webapp.main import normalize_public_row

    source = {"risk_band": "critical", "review_priority": "legacy wording", "transaction_count": 10}
    published = normalize_public_row("review_strategy", source)
    assert verify.compare_public_copy("review_strategy", [published], [source])["status"] == "MATCH"
    assert verify.compare_public_copy(
        "review_strategy", [published], [{**source, "transaction_count": 11}],
    )["status"] == "DIFF"


def test_presentation_diagnostic_preserves_strict_failure() -> None:
    result = verify.inspect(FakeClient(changed="rpt_review_strategy"), historical(), explain_public_copy=True)
    group = result["groups"]["review_strategy"]
    assert group["status"] == "DIFF_DIRECT"
    assert group["public_presentation_comparison"]["status"] == "DIFF"
    assert result["status"] == "DIRECT_TABLES_UNRESOLVED"
    assert result["verified_full_27_group_parity"] is False
