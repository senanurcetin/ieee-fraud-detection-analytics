"""Data-free tests: audit 27 presentation groups without a query, token or fake freshness."""

from __future__ import annotations

import copy
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
audit_tool = importlib.import_module("scripts.audit_reporting_snapshot")
web = importlib.import_module("webapp.main")


def fixture_payload() -> dict:
    payload: dict = {
        "meta": {
            "project_id": "workintech-working",
            "dataset": "fraud_project_reporting",
            "total_transactions": 100,
            "fraud_transactions": 3,
            "refreshed_at": "2026-09-10T19:41:45Z",
        }
    }
    for key in audit_tool.SOURCES:
        payload[key] = []
    return payload


def test_mapping_matches_actual_web_api_and_24_physical_sources() -> None:
    assert audit_tool.SOURCES == web.BIGQUERY_TABLES
    assert len(audit_tool.SOURCES) == 27
    assert len(set(audit_tool.SOURCES.values())) == 24
    assert sum(value == "fact_train_transactions" for value in audit_tool.SOURCES.values()) == 4
    assert set(audit_tool.SOURCES) == set(web.TABLE_QUERIES)
    assert set(audit_tool.KEYS) == set(audit_tool.SOURCES)
    for group in audit_tool.SOURCE_SHAPE:
        assert group in audit_tool.SOURCES


def test_committed_snapshot_audit_does_not_claim_source_evidence() -> None:
    snapshot = audit_tool.read_json(audit_tool.SNAPSHOT_PATH)
    report = audit_tool.audit(snapshot)
    assert report["comparison_status"] == "NOT_RUN"
    assert report["provenance_verdict"] == "UNVERIFIED_EXTERNAL_SOURCE"
    assert report["source_query_jobs_executed"] == 0
    assert report["reporting_group_count"] == 27
    assert report["unique_physical_table_references"] == 24
    assert report["historical_snapshot_refresh"] == "2026-09-10T19:41:45Z"
    assert report["duplicate_fact_groups"] == [
        "niche_drilldown", "payment_email_matrix", "proxy_cross_matrix", "proxy_product_matrix"
    ]
    assert not report["extra_historical_groups"]
    assert report["status_counts"] == {"NOT_CHECKED": 27}


def test_order_independent_comparison_rounds_only_numeric_cells() -> None:
    older = [
        {"product_cd": "W", "fraud_rate": 0.12345678, "count": 4, "enabled": True},
        {"product_cd": "C", "fraud_rate": 0.25, "count": 8, "enabled": False},
    ]
    newer = [
        {"product_cd": "C", "fraud_rate": 0.2500000001, "count": 8.0, "enabled": False},
        {"enabled": True, "count": 4, "fraud_rate": 0.12345679, "product_cd": "W"},
    ]
    matched = audit_tool.compare_group("product_risk", older, newer)
    assert matched["status"] == "MATCH"
    assert matched["historical_only_rows"] == matched["current_only_rows"] == 0


def test_precise_field_level_diff_without_reporting_values() -> None:
    older = [{"product_cd": "SECRET_SEGMENT", "fraud_rate": 0.1, "transaction_count": 10}]
    newer = [{"product_cd": "SECRET_SEGMENT", "fraud_rate": 0.2, "transaction_count": 10}]
    report = audit_tool.compare_group("product_risk", older, newer)
    assert report["status"] == "DIFF"
    assert report["changed_field_counts"] == {"fraud_rate": 1}
    assert report["historical_only_rows"] == 1
    assert report["current_only_rows"] == 1
    assert report["examples"][0]["field"] == "fraud_rate"
    text = json.dumps(report)
    assert "SECRET_SEGMENT" not in text
    assert '"fraud_rate": 0.1' not in text
    assert len(report["examples"][0]["key_sha256"]) == 16


def test_schema_drift_and_missing_key_detection() -> None:
    changed = audit_tool.compare_group(
        "identity_risk",
        [{"has_identity": 1, "fraud_count": 3, "legacy_field": 7}],
        [{"has_identity": 1, "fraud_count": 3, "new_metric": 0}],
    )
    assert changed["status"] == "DIFF"
    assert changed["missing_fields_in_current"] == ["legacy_field"]
    assert changed["new_fields_in_current"] == ["new_metric"]
    missing_key = audit_tool.compare_group(
        "product_risk",
        [{"transaction_count": 3}],
        [{"transaction_count": 4}],
    )
    assert missing_key["match_basis"] == "full_row_multiset_only_duplicate_or_missing_keys"


def test_multiset_counts_duplicates_without_losing_rows() -> None:
    historical = [
        {"product_cd": "W", "transaction_count": 1},
        {"product_cd": "W", "transaction_count": 1},
    ]
    fresh = [{"product_cd": "W", "transaction_count": 1}]
    report = audit_tool.compare_group("product_risk", historical, fresh)
    assert report["status"] == "DIFF"
    assert report["historical_only_rows"] == 1
    assert report["current_only_rows"] == 0
    assert report["match_basis"] == "full_row_multiset_only_duplicate_or_missing_keys"


def test_missing_current_group_is_incomplete_not_green() -> None:
    before = fixture_payload()
    after = copy.deepcopy(before)
    after.pop("segment_watchlist")
    result = audit_tool.audit(before, after)
    assert result["comparison_status"] == "INCOMPLETE"
    assert result["groups"]["segment_watchlist"]["status"] == "MISSING_CURRENT"
    assert result["status_counts"]["MATCH"] == 26


def test_changed_group_and_metadata_are_detected() -> None:
    before = fixture_payload()
    after = copy.deepcopy(before)
    before["product_risk"] = [{"product_cd": "C", "fraud_count": 1}]
    after["product_risk"] = [{"product_cd": "C", "fraud_count": 2}]
    after["meta"]["fraud_transactions"] = 4
    result = audit_tool.audit(before, after)
    assert result["comparison_status"] == "DIFF"
    assert result["metadata_mismatch_fields"] == ["fraud_transactions"]
    assert result["groups"]["product_risk"]["changed_field_counts"]["fraud_count"] == 1


def test_identical_payload_is_not_source_provenance() -> None:
    before = fixture_payload()
    after = copy.deepcopy(before)
    after["meta"]["refreshed_at"] = "2026-10-17T00:00:00Z"
    report = audit_tool.audit(before, after)
    assert report["comparison_status"] == "STRUCTURAL_MATCH"
    assert report["provenance_verdict"] == "UNVERIFIED_EXTERNAL_SOURCE"
    assert report["same_published_payload"]
    assert "not" in report["warning"].lower()


def test_numeric_strings_bool_null_and_nonfinite_differ() -> None:
    assert audit_tool.canonical("1") != audit_tool.canonical(1)
    assert audit_tool.canonical(True) != audit_tool.canonical(1)
    assert audit_tool.canonical(None) != audit_tool.canonical("None")
    assert audit_tool.canonical(float("nan")) == ("nonfinite", "nan")


def test_cli_writes_offline_report_without_current_comparison(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    snap = tmp_path / "history.json"
    output = tmp_path / "report.json"
    snap.write_text(json.dumps(fixture_payload()), encoding="utf-8")
    code = audit_tool.main(["--snapshot", str(snap), "--output", str(output)])
    assert code == 1  # no external evidence means non-passing parity
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["comparison_status"] == "NOT_RUN"
    assert "SECRET" not in capsys.readouterr().out


def test_cli_accepts_structural_comparison_but_never_claims_freshness(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    snap, current = tmp_path / "history.json", tmp_path / "current.json"
    data = fixture_payload()
    snap.write_text(json.dumps(data), encoding="utf-8")
    current.write_text(json.dumps(data), encoding="utf-8")
    code = audit_tool.main(["--snapshot", str(snap), "--current-json", str(current)])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["comparison_status"] == "STRUCTURAL_MATCH"
    assert result["provenance_verdict"] == "UNVERIFIED_EXTERNAL_SOURCE"


def test_malformed_payload_is_not_accepted(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    snap = tmp_path / "bad.json"
    snap.write_text("private-secret malformed {", encoding="utf-8")
    assert audit_tool.main(["--snapshot", str(snap)]) == 2
    assert "private-secret" not in capsys.readouterr().err
