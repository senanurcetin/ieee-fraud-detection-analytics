"""Snapshot-only release smoke policy, offline and synthetic negative cases."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
smoke = importlib.import_module("scripts.verify_snapshot_release")


def evidence() -> dict:
    return {
        "source_status": "historical_over_30d",
        "source_as_of": "2026-09-10T19:41:45Z",
        "source_parity": "not_verified_against_current_bigquery",
        "report_groups": 27,
        "physical_source_tables": 24,
        "model_output_contract": "uncalibrated_ranking_score_not_validated_probability",
        "live_transaction_monitoring": False,
        "production_model_evidence": False,
    }


def dashboard() -> dict:
    return {
        **{f"group_{i}": [] for i in range(27)},
        "meta": {
            "total_transactions": 590540,
            "fraud_transactions": 20663,
            "refreshed_at": "2026-09-10T19:41:45Z",
        },
    }


def html() -> str:
    return "<html><body><h1>NEXUS</h1><p id='nexus-evidence-context'></p></body></html>"


def test_demo_smoke_accepts_only_explicitly_historical_complete_contract() -> None:
    result = smoke.verify_payloads(evidence(), dashboard(), html())
    assert result["result"] == "PASS_HISTORICAL_OFFLINE_DEMO"
    assert result["checks_failed"] == []
    assert result["model_promoted"] is False
    assert result["production_deployed"] is False
    assert result["bigquery_parity_verified"] is False


def test_demo_smoke_rejects_false_live_or_calibration_claims() -> None:
    data = evidence()
    data.update({
        "source_parity": "verified",
        "live_transaction_monitoring": True,
        "production_model_evidence": True,
        "model_output_contract": "calibrated_probability",
    })
    result = smoke.verify_payloads(data, dashboard(), html())
    assert result["result"] == "FAIL_RELEASE_SMOKE"
    assert len(result["checks_failed"]) >= 3


def test_demo_smoke_rejects_mismatched_or_missing_snapshots() -> None:
    data = dashboard()
    data.pop("group_5")
    result = smoke.verify_payloads(evidence(), data, html())
    assert "Expected 27" in " ".join(result["checks_failed"])
    data = dashboard()
    data["meta"]["fraud_transactions"] = 0
    assert smoke.verify_payloads(evidence(), data, html())["result"] == "FAIL_RELEASE_SMOKE"
    assert smoke.verify_payloads(evidence(), dashboard(), "<html>NEXUS</html>")["result"] == "FAIL_RELEASE_SMOKE"


def test_actual_committed_historical_snapshot_matches_offline_contract() -> None:
    # This checks only committed historical artifacts, not current BigQuery data.
    source = json.loads((ROOT / "webapp/snapshots/dashboard.json").read_text(encoding="utf-8"))
    result = smoke.verify_payloads(evidence(), source, html())
    assert result["result"] == "PASS_HISTORICAL_OFFLINE_DEMO"
