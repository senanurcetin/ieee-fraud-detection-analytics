"""Public reporting stays local and recovers safely after snapshot rebuilds."""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
api = importlib.import_module("webapp.main")


@pytest.fixture
def snapshot_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("WEB_SNAPSHOT_DISABLE", raising=False)
    monkeypatch.delenv("WEB_INTERNAL_REFRESH_TOKEN", raising=False)
    monkeypatch.setenv("WEB_DATA_BACKEND", "bigquery")
    monkeypatch.setattr(api, "SNAPSHOT_DIR", tmp_path)
    monkeypatch.setattr(api, "_SNAPSHOT_CACHE", {})
    monkeypatch.setattr(api, "_SNAPSHOT_SIGNATURES", {})
    monkeypatch.setattr(api, "run_query", lambda *args: pytest.fail("Public request reached warehouse"))
    return tmp_path


def test_missing_snapshot_recovers_after_artifact_is_created(snapshot_dir: Path) -> None:
    assert api.load_snapshot("enterprise-cases") is None
    payload = {"cases": [{"transaction_id": 42}]}
    (snapshot_dir / "enterprise-cases.json").write_text(json.dumps(payload), encoding="utf-8")
    assert api.load_snapshot("enterprise-cases") == payload


def test_snapshot_cache_reloads_replacement_and_forgets_deleted_evidence(snapshot_dir: Path) -> None:
    path = snapshot_dir / "enterprise-cases.json"
    path.write_text('{"cases": [{"transaction_id": 1}]}', encoding="utf-8")
    assert api.load_snapshot("enterprise-cases")["cases"][0]["transaction_id"] == 1
    replacement = snapshot_dir / "rebuilt.json"
    replacement.write_text('{"cases": [{"transaction_id": 12345}]}', encoding="utf-8")
    replacement.replace(path)
    assert api.load_snapshot("enterprise-cases")["cases"][0]["transaction_id"] == 12345
    path.unlink()
    assert api.load_snapshot("enterprise-cases") is None
    assert TestClient(api.app).get("/api/enterprise/cases?limit=10").status_code == 503


@pytest.mark.parametrize("content", ["{", "[]", "{}", '{"cases": null}', '{"cases": [42]}'])
def test_malformed_snapshot_fails_closed_then_recovers(snapshot_dir: Path, content: str) -> None:
    path = snapshot_dir / "enterprise-cases.json"
    path.write_text(content, encoding="utf-8")
    response = TestClient(api.app).get("/api/enterprise/cases?limit=10")
    assert response.status_code == 503
    path.write_text('{"cases": [{"transaction_id": 99}]}', encoding="utf-8")
    assert TestClient(api.app).get("/api/enterprise/cases?limit=10").json()["count"] == 1


def test_dashboard_requires_reporting_groups_and_source_metadata(snapshot_dir: Path) -> None:
    path = snapshot_dir / "dashboard.json"
    payload = {key: [] for key in api.BIGQUERY_TABLES}
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert TestClient(api.app).get("/api/dashboard").status_code == 503
    payload["meta"] = {"backend": "snapshot"}
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert TestClient(api.app).get("/api/dashboard").json() == payload


def test_health_is_network_free_with_configured_cloud_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_DATA_BACKEND", "bigquery")
    monkeypatch.setenv("GCP_PROJECT_ID", "offline-project")
    monkeypatch.setenv("BQ_DATASET", "reporting")
    monkeypatch.setattr(api, "_LOCATION_CACHE", {})
    monkeypatch.setattr(api, "bq_client", lambda: pytest.fail("Liveness attempted cloud authentication"))
    response = TestClient(api.app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["resolved_location"] is None
    api._LOCATION_CACHE["offline-project.reporting"] = "EU"
    assert TestClient(api.app).get("/api/health").json()["resolved_location"] == "EU"


@pytest.mark.parametrize("route", [
    "/api/dashboard", "/api/enterprise/summary", "/api/enterprise/segments",
    "/api/enterprise/alerts", "/api/enterprise/model-monitoring",
])
@pytest.mark.parametrize("warm_cache", [False, True])
def test_snapshot_deleted_after_route_guard_never_falls_back_to_cloud(
    snapshot_dir: Path, monkeypatch: pytest.MonkeyPatch, route: str, warm_cache: bool,
) -> None:
    dashboard = {key: [] for key in api.BIGQUERY_TABLES}
    dashboard["meta"] = {"backend": "snapshot"}
    (snapshot_dir / "dashboard.json").write_text(json.dumps(dashboard), encoding="utf-8")
    segments = {key: [] for key in api.SNAPSHOT_ROWS["enterprise-segments"]}
    (snapshot_dir / "enterprise-segments.json").write_text(json.dumps(segments), encoding="utf-8")
    monkeypatch.setattr(api, "_CACHE", {
        "expires_at": time.time() + 600 if warm_cache else 0.0,
        "payload": dashboard if warm_cache else None,
    })
    monkeypatch.setattr(api, "direct_aggregate", lambda *args: pytest.fail("Public request reached warehouse"))
    guard = api.require_snapshot_or_internal_access

    def delete_after_guard(name: str, refresh: bool, supplied_token: str | None) -> None:
        guard(name, refresh, supplied_token)
        (snapshot_dir / f"{name}.json").unlink()

    monkeypatch.setattr(api, "require_snapshot_or_internal_access", delete_after_guard)
    assert TestClient(api.app).get(route).status_code == 403


def test_authorized_warehouse_cache_fill_survives_missing_snapshot(
    snapshot_dir: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WEB_INTERNAL_REFRESH_TOKEN", "internal-test-token")
    monkeypatch.setattr(api, "_CACHE", {"expires_at": 0.0, "payload": None})
    monkeypatch.setattr(api, "build_dashboard_payload", lambda: {"source": "authorized-warehouse"})
    response = TestClient(api.app).get(
        "/api/dashboard", headers={"X-Internal-Refresh-Token": "internal-test-token"},
    )
    assert response.status_code == 200
    assert response.json() == {"source": "authorized-warehouse"}
