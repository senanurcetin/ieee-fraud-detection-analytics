"""F07 analyst review is read-only, historical, scoped and keyboard operable."""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
api = importlib.import_module("webapp.main")
client = TestClient(api.app)


def test_review_queue_is_a_snapshot_only_historical_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = {
        "cases": [
            {
                "transaction_id": 2401, "model_probability": 0.82,
                "risk_band": "High", "product_cd": "C", "is_fraud": 1,
            }
        ],
        "meta": {"source": "historical_snapshot"},
    }
    monkeypatch.setattr(api, "load_snapshot", lambda name: sample if name == "enterprise-cases" else None)
    monkeypatch.setattr(api, "run_query", lambda *args: pytest.fail("Paid BigQuery SQL must not execute"))
    response = client.get("/api/enterprise/cases?limit=40")
    assert response.status_code == 200
    assert response.json()["cases"][0]["transaction_id"] == 2401


def test_legacy_helper_no_longer_calls_uncalibrated_score_probability() -> None:
    factors = api.build_transaction_explanation(
        {"model_probability": 0.65, "risk_band": "Low", "transaction_amount": 20}
    )
    assert any(item["factor"] == "Uncalibrated model score" for item in factors)
    details = " ".join(str(item["detail"]) for item in factors)
    assert "not a calibrated fraud probability" in details
    assert "65.00% fraud probability" not in details


def test_analyst_workspace_uses_bounded_historical_read_only_records() -> None:
    html = (ROOT / "webapp/static/decision-studio.html").read_text(encoding="utf-8")
    js = (ROOT / "webapp/static/risk-decision-studio.js").read_text(encoding="utf-8")
    css = (ROOT / "webapp/static/review-queue.css").read_text(encoding="utf-8")
    assert 'id="historical-review-heading"' in html
    assert 'id="historical-review-queue"' in html
    assert 'id="historical-review-detail"' in html
    assert 'href="/static/review-queue.css"' in html
    assert "/api/enterprise/cases?limit=40" in js
    assert "rows.filter(" not in js or "slice(0,40)" in js
    assert "aria-pressed" in js
    assert "button.addEventListener('click'" in js
    assert "item.is_fraud" not in js
    assert "item.actual_is_fraud" not in js
    assert "case status is recorded" in js
    assert "Uncalibrated model score" in js
    assert "No warehouse fallback or simulated cases" in js
    assert "textContent" in js
    assert "@media(max-width:760px)" in css


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed in this runner")
def test_review_studio_javascript_parses_without_syntax_errors() -> None:
    result = subprocess.run(
        ["node", "--check", str(ROOT / "webapp/static/risk-decision-studio.js")],
        capture_output=True,
        text=True,
        check=False,
        timeout=8,
    )
    assert result.returncode == 0, result.stderr
