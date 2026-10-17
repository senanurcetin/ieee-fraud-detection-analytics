"""Public deployment SHA attestation and no-network negative tests."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
api = importlib.import_module("webapp.main")
public = importlib.import_module("scripts.verify_public_release")
client = TestClient(api.app)
SHA = "a" * 40


def test_evidence_api_discloses_only_formatted_provider_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", SHA.upper())
    monkeypatch.setattr(api, "run_query", lambda *a, **kw: pytest.fail("No paid SQL on public status"))
    body = client.get("/api/evidence-status").json()
    assert body["deployed_git_commit"] == SHA
    assert body["source_parity"] == "not_verified_against_current_bigquery"
    assert body["live_transaction_monitoring"] is False
    assert "token" not in json.dumps(body).lower()


@pytest.mark.parametrize("bad", ["", "no-commit", "a" * 39, "a" * 41, "Z" * 40])
def test_provider_sha_missing_or_invalid_fails_closed(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", bad)
    assert client.get("/api/evidence-status").json()["deployed_git_commit"] is None


def fixtures() -> tuple[dict, dict, str, str]:
    historical = json.loads((ROOT / "webapp/snapshots/dashboard.json").read_text("utf-8"))
    evidence = api.public_evidence_status(historical)
    evidence["deployed_git_commit"] = SHA
    html = (ROOT / "webapp/static/index.html").read_text("utf-8")
    studio = (ROOT / "webapp/static/decision-studio.html").read_text("utf-8")
    return evidence, historical, html, studio


def test_public_smoke_exact_sha_and_historical_screens_pass_offline() -> None:
    result = public.evaluate_public_release(SHA, *fixtures())
    assert result["result"] == "PASS_PUBLIC_HISTORICAL_RELEASE"
    assert result["expected_git_sha"] == SHA
    assert result["observed_git_sha"] == SHA
    assert result["verified_live_bigquery"] is False
    assert result["verified_model_calibration"] is False


def test_public_smoke_rejects_old_sha_invalid_or_missing_ui() -> None:
    evidence, data, html, studio = fixtures()
    assert public.evaluate_public_release("b" * 40, evidence, data, html, studio)[
        "result"
    ] == "FAIL_PUBLIC_RELEASE"
    assert public.evaluate_public_release(SHA, {**evidence, "deployed_git_commit": None}, data, html, studio)[
        "result"
    ] == "FAIL_PUBLIC_RELEASE"
    assert public.evaluate_public_release(SHA, evidence, data, html, "<html/>")[
        "result"
    ] == "FAIL_PUBLIC_RELEASE"
    with pytest.raises(ValueError):
        public.evaluate_public_release("bad", evidence, data, html, studio)


def test_public_smoke_never_follows_sso_or_external_host() -> None:
    handler = public.NoRedirect()
    assert handler.redirect_request(None, None, 302, "location", {}, "https://vercel.com/login") is None
    assert public.PRODUCTION_HOST == "fraud-project-web.vercel.app"
    with pytest.raises(ValueError):
        public._get("/api/enterprise/cases/123456")


def test_public_smoke_handles_network_or_protected_url_without_false_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        public,
        "_get",
        lambda path: (_ for _ in ()).throw(OSError("external SSO protected")),
    )
    result = public.inspect_public_release(SHA)
    assert result["result"] == "FAIL_PUBLIC_RELEASE"
    assert result["checked_hostname"] == public.PRODUCTION_HOST
    assert "external SSO protected" not in json.dumps(result)


def test_remote_workflow_requires_exact_main_and_no_secrets() -> None:
    workflow = (ROOT / ".github/workflows/public-release-smoke.yml").read_text("utf-8")
    assert "github.sha" in workflow
    assert "python -m scripts.verify_public_release" in workflow
    assert "permissions:" in workflow and "contents: read" in workflow
    assert "vercel deploy" not in workflow
    assert "secrets." not in workflow
    assert "kaggle" not in workflow.lower()
    assert "dbt run" not in workflow
