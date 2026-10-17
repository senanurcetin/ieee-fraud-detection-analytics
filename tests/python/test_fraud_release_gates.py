"""F01: fail-closed public refresh and truthful release gates (offline)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
app_module = importlib.import_module("webapp.main")
client = TestClient(app_module.app)

REFRESH_ROUTES = (
    "/api/dashboard",
    "/api/enterprise/summary",
    "/api/enterprise/segments",
    "/api/enterprise/alerts",
    "/api/enterprise/model-monitoring",
)


@pytest.mark.parametrize("route", REFRESH_ROUTES)
def test_anonymous_live_refresh_is_denied_without_query(
    route: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WEB_INTERNAL_REFRESH_TOKEN", raising=False)
    monkeypatch.setattr(
        app_module,
        "cached_dashboard_payload",
        lambda refresh=False: pytest.fail("Unauthenticated refresh reached reporting."),
    )
    response = client.get(f"{route}?refresh=true")
    assert response.status_code == 403
    assert "internal token" in response.json()["detail"]


@pytest.mark.parametrize("route", REFRESH_ROUTES)
def test_wrong_refresh_token_is_denied(
    route: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WEB_INTERNAL_REFRESH_TOKEN", "private-refresh-secret")
    response = client.get(
        f"{route}?refresh=true",
        headers={"X-Internal-Refresh-Token": "wrong-value"},
    )
    assert response.status_code == 403


def test_valid_token_allows_explicit_internal_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_INTERNAL_REFRESH_TOKEN", "private-refresh-secret")
    calls: list[bool] = []

    def guarded_payload(refresh: bool = False) -> dict:
        calls.append(refresh)
        return {"source": "internal-verified"}

    monkeypatch.setattr(app_module, "cached_dashboard_payload", guarded_payload)
    response = client.get(
        "/api/dashboard?refresh=true",
        headers={"X-Internal-Refresh-Token": "private-refresh-secret"},
    )
    assert response.status_code == 200
    assert response.json() == {"source": "internal-verified"}
    assert calls == [True]


def test_public_snapshot_read_still_works_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEB_INTERNAL_REFRESH_TOKEN", raising=False)
    monkeypatch.setattr(
        app_module,
        "cached_dashboard_payload",
        lambda refresh=False: {"refresh": refresh, "source": "historical-snapshot"},
    )
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json() == {"refresh": False, "source": "historical-snapshot"}


def test_snapshot_builder_supplies_ephemeral_header() -> None:
    source = (ROOT / "scripts" / "build_web_snapshot.py").read_text(encoding="utf-8")
    assert "secrets.token_urlsafe(32)" in source
    assert 'os.environ["WEB_INTERNAL_REFRESH_TOKEN"] = refresh_token' in source
    assert '"X-Internal-Refresh-Token": refresh_token' in source


def test_manual_release_requires_credentials_and_no_automatic_false_green() -> None:
    workflow = (ROOT / ".github" / "workflows" / "vercel-deploy.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in workflow
    assert "\n  push:\n" not in workflow
    assert "Vercel release: BLOCKED" in workflow
    assert "exit 1" in workflow
    assert "npx vercel deploy --prod" in workflow


def test_requested_real_data_build_fails_if_credentials_missing() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "Full IEEE-CIS data build: BLOCKED" in workflow
    assert "exit 1" in workflow
    assert "Full IEEE-CIS data build: NOT RUN" in workflow
