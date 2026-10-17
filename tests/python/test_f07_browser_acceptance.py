"""Historical browser acceptance contract; no production Vercel or warehouse dependency."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
app = importlib.import_module("webapp.main")
client = TestClient(app.app)


def test_decision_studio_is_real_fastapi_route() -> None:
    response = client.get("/studio?view=overview")
    assert response.status_code == 200
    assert 'id="historical-review-queue"' in response.text
    assert 'id="studio-evidence-source"' in response.text
    assert "/static/risk-decision-studio.js" in response.text


def test_main_dashboard_has_accessible_studio_link() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/studio?view=overview"' in response.text
    assert 'aria-label="Open historical Risk Decision Studio"' in response.text


def test_new_browser_workflow_runs_all_engines_without_paid_cloud_data() -> None:
    file = (ROOT / ".github/workflows/browser-acceptance.yml").read_text(encoding="utf-8")
    assert "playwright==1.56.0" in file
    assert "install --with-deps chromium firefox webkit" in file
    assert "python -m unittest discover -s tests/browser -p 'test_*.py' -v" in file
    assert "verify_snapshot_release" in file
    assert "WEB_DATA_BACKEND: bigquery" in file
    assert "127.0.0.1:8000" in file
    assert "timeout-minutes: 30" in file
    assert "secrets." not in file
    assert "vercel deploy" not in file
    assert "dbt run" not in file
    assert "kaggle" not in file.lower()


def test_browser_regressions_cover_review_and_responsive_source() -> None:
    file = (ROOT / "tests/browser/test_f07_studio.py").read_text(encoding="utf-8")
    assert "/studio?view=overview" in file
    assert "#historical-review-queue .studio-review-item" in file
    assert '"aria-pressed"' in file
    assert '"width": 375' in file
    assert "Uncalibrated model score" in file
    assert "#nexus-evidence-context" in file
