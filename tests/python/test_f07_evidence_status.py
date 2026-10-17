"""F07 historical source disclosure and frontend fail-closed display contracts.

No BigQuery work, source mutations or synthetic data presented as live.
"""
from __future__ import annotations

import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
api = importlib.import_module("webapp.main")
client = TestClient(api.app)


def snapshot(timestamp: str = "2026-09-10T19:41:45Z") -> dict:
    return {
        "meta": {
            "refreshed_at": timestamp,
            "project_id": "workintech-working",
            "dataset": "fraud_project_reporting",
            "backend": "snapshot",
        },
        "report_readiness": [{"status": "PASS"}, {"status": "FAIL"}],
    }


def test_historical_snapshot_is_never_marked_live() -> None:
    result = api.public_evidence_status(snapshot(), now=datetime(2026, 10, 17, tzinfo=UTC))
    assert result["source_status"] == "historical_over_30d"
    assert result["source_as_of"] == "2026-09-10T19:41:45Z"
    assert result["age_days"] == 36
    assert result["report_groups"] == 27
    assert result["physical_source_tables"] == 24
    assert result["source_parity"] == "not_verified_against_current_bigquery"
    assert result["presentation_quality_passed"] == 1
    assert result["presentation_quality_total"] == 2
    assert result["live_transaction_monitoring"] is False
    assert result["production_model_evidence"] is False
    assert "uncalibrated" in result["model_output_contract"]


def test_snapshot_within_30days_is_still_historical() -> None:
    result = api.public_evidence_status(
        snapshot("2026-10-16T12:00:00+00:00"), now=datetime(2026, 10, 17, tzinfo=UTC)
    )
    assert result["source_status"] == "historical_dated"
    assert result["source_parity"].startswith("not_verified")
    assert result["live_transaction_monitoring"] is False


@pytest.mark.parametrize("bad", [None, {}, {"meta": {}}, snapshot("not-a-date"), snapshot("2026-10-19T00:00:00Z")])
def test_missing_malformed_or_future_timestamp_fail_closed(bad: dict | None) -> None:
    result = api.public_evidence_status(bad, now=datetime(2026, 10, 17, tzinfo=UTC))
    assert result["source_status"] in {"unavailable", "timestamp_unverified"}
    assert result["source_as_of"] is None
    assert result["age_days"] is None
    assert result["live_transaction_monitoring"] is False


def test_evidence_api_never_uses_bigquery_and_is_publicly_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api, "load_snapshot", lambda name: snapshot() if name == "dashboard" else None)
    monkeypatch.setattr(api, "run_query", lambda *a, **k: pytest.fail("warehouse read"))
    monkeypatch.setattr(api, "direct_aggregate", lambda *a, **k: pytest.fail("warehouse read"))
    response = client.get("/api/evidence-status")
    assert response.status_code == 200
    body = response.json()
    assert body["source_status"] == "historical_over_30d"
    assert "tokens" not in body
    assert "data" not in body
    assert "credential" not in str(body).lower()
    assert body["source_parity"] == "not_verified_against_current_bigquery"


def test_source_status_api_reports_absent_snapshot_without_warehouse_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api, "load_snapshot", lambda name: None)
    monkeypatch.setattr(api, "run_query", lambda *a, **k: pytest.fail("warehouse read"))
    result = client.get("/api/evidence-status")
    assert result.status_code == 200
    assert result.json()["source_status"] == "unavailable"
    assert result.json()["source_as_of"] is None


def test_both_nexus_views_render_source_age_and_model_limitations() -> None:
    report = (ROOT / "webapp/static/index.html").read_text(encoding="utf-8")
    studio = (ROOT / "webapp/static/decision-studio.html").read_text(encoding="utf-8")
    js = (ROOT / "webapp/static/risk-decision-studio.js").read_text(encoding="utf-8")
    css = (ROOT / "webapp/static/nexus-evidence.css").read_text(encoding="utf-8")
    assert "/api/evidence-status" in report and "/api/evidence-status" in js
    assert 'id="nexus-evidence-context"' in report
    assert 'id="nexus-evidence-time"' in report
    assert 'id="nexus-evidence-parity"' in report
    assert 'id="nexus-evidence-model"' in report
    assert 'id="studio-evidence-source"' in studio
    assert "Uncalibrated ranking" in report
    assert "BigQuery parity unverified" in js
    assert "No live" in studio or "no live" in studio.lower()
    assert "@media (max-width:680px)" in css
    assert "textContent" in report and "textContent" in js
    assert "Data freshness is not yet verified" in report
