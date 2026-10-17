"""F08 runtime dependency boundaries, packaging and private-artifact tests."""
from __future__ import annotations

import ast
import importlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
store = importlib.import_module("webapp.explanation_store")
api = importlib.import_module("webapp.main")
client = TestClient(api.app)


def test_web_app_does_not_import_heavy_ml_dependencies() -> None:
    source = (ROOT / "webapp/main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    # A conditional DuckDB import inside an explicitly selected local backend
    # is not an eager dependency of the snapshot-only web server entrypoint.
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert "webapp.explanation_store" in imports
    assert "src.local_shap" not in imports
    assert not any(name.split(".")[0] in {"numpy", "shap", "lightgbm", "duckdb"} for name in imports)
    reader = (ROOT / "webapp/explanation_store.py").read_text(encoding="utf-8")
    assert "mode=ro" in reader
    assert "SELECT payload_json" in reader
    assert "sqlite3.connect" in reader


def test_private_explanations_remain_readable_without_model_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "local.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE local_explanations (transaction_id INTEGER PRIMARY KEY, model_version TEXT, payload_json TEXT)")
        db.execute("INSERT INTO local_explanations VALUES (?,?,?)", (18, "synthetic", json.dumps({"method": "TreeSHAP", "score": 0.3})))
    assert store.load_explanation(path, 18) == {"method": "TreeSHAP", "score": 0.3}
    assert store.load_explanation(path, 42) is None
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(OSError):
        store.load_explanation(missing, 42)
    assert not missing.exists()


def test_local_explanation_endpoint_requires_auth_without_ml_imports(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("WEB_INTERNAL_REFRESH_TOKEN", "f08-demo-secret")
    monkeypatch.setenv("WEB_LOCAL_SHAP_DB_PATH", str(tmp_path / "missing.sqlite"))
    assert client.get("/api/enterprise/cases/18/local-explanation").status_code == 403
    response = client.get(
        "/api/enterprise/cases/18/local-explanation",
        headers={"X-Internal-Refresh-Token": "f08-demo-secret"},
    )
    assert response.status_code == 503


def test_container_is_non_root_snapshot_only_and_loopback_exposed() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    runtime_requirements = (ROOT / "webapp/requirements.txt").read_text(encoding="utf-8")
    assert "python:3.11-slim-bookworm" in dockerfile
    assert "USER nexus" in dockerfile
    assert "COPY webapp/ ./webapp/" in dockerfile
    assert "COPY src/" not in dockerfile
    assert "COPY . ." not in dockerfile
    assert "WEB_DATA_BACKEND=bigquery" in dockerfile
    assert "127.0.0.1:8000:8000" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose
    assert "ALL" in compose
    assert "WEB_SNAPSHOT_DISABLE:" in compose
    assert "!webapp/" in ignore
    assert "webapp/.env.*" in ignore
    assert "src/" not in ignore or ignore.startswith("#")
    assert "shap==" not in runtime_requirements
    assert "lightgbm==" not in runtime_requirements
    assert "numpy==" not in runtime_requirements


def test_snapshot_only_evidence_and_dashboard_routes_do_not_need_bigquery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WEB_DATA_BACKEND", "bigquery")
    monkeypatch.delenv("WEB_SNAPSHOT_DISABLE", raising=False)
    monkeypatch.setattr(api, "run_query", lambda *a, **k: pytest.fail("Unexpected warehouse query"))
    assert client.get("/api/evidence-status").status_code == 200
    assert client.get("/api/dashboard").status_code == 200


def test_local_container_paths_are_not_part_of_public_metadata() -> None:
    snapshot = client.get("/api/evidence-status").json()
    assert "WEB_INTERNAL_REFRESH_TOKEN" not in str(snapshot)
    assert "WEB_LOCAL_SHAP_DB_PATH" not in str(snapshot)
    assert "credentials" not in snapshot
