"""Safe, network-free tests for GitHub OIDC/WIF read-only BigQuery parity.

No credentials are created or exercised by these tests.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
verify = importlib.import_module("scripts.verify_reporting_tables_bigquery_readonly")


@pytest.mark.parametrize("explain_copy", [False, True])
def test_adc_uses_only_bigquery_readonly_oauth_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, explain_copy: bool,
) -> None:
    import google.auth
    from google.cloud import bigquery

    captured: dict[str, object] = {}
    sentinel_credentials = object()

    def fake_adc(*, scopes):
        captured["scopes"] = scopes
        return sentinel_credentials, "other-project-never-use-default"

    def fake_client(*, project, credentials):
        captured["project"] = project
        captured["credentials"] = credentials
        return SimpleNamespace(marker="fake-client")

    def fake_inspect(client, snapshot, *, project, dataset, max_source_rows, explain_public_copy):
        assert client.marker == "fake-client"
        assert snapshot["meta"]["project_id"] == project
        assert dataset == "fraud_project_reporting"
        assert max_source_rows == 10000
        assert explain_public_copy is explain_copy
        return {
            "status": "DIRECT_TABLES_MATCH_PARTIAL_ONLY",
            "sql_query_jobs_submitted": 0,
            "verified_full_27_group_parity": False,
        }

    monkeypatch.setattr(google.auth, "default", fake_adc)
    monkeypatch.setattr(bigquery, "Client", fake_client)
    monkeypatch.setattr(verify, "inspect", fake_inspect)

    source = tmp_path / "snapshot.json"
    source.write_text(json.dumps({"meta": {"project_id": "workintech-working"}}), encoding="utf-8")
    output = tmp_path / "parity.json"
    code = verify.main([
        "--use-adc", "--project", "workintech-working",
        "--dataset", "fraud_project_reporting",
        "--snapshot", str(source), "--output", str(output),
        *(["--explain-public-copy"] if explain_copy else []),
    ])
    assert code == 0
    assert captured == {
        "scopes": ["https://www.googleapis.com/auth/bigquery.readonly"],
        "project": "workintech-working",
        "credentials": sentinel_credentials,
    }
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["verified_full_27_group_parity"] is False


def test_adc_auth_failure_never_echoes_sensitive_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    import google.auth

    def fail_auth(*, scopes):
        raise RuntimeError("mock-token-DO-NOT-LOG")

    monkeypatch.setattr(google.auth, "default", fail_auth)
    source = tmp_path / "snapshot.json"
    source.write_text("{}", encoding="utf-8")
    assert verify.main(["--use-adc", "--snapshot", str(source)]) == 2
    err = capsys.readouterr().err
    assert "mock-token" not in err
    assert err.strip() == "Read-only BigQuery parity inspection unavailable"


def test_service_account_legacy_contract_still_requires_existing_private_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    key = tmp_path / "private-test-key.json"
    code = verify.main(["--credentials-file", str(key)])
    assert code == 2
    assert str(key) not in capsys.readouterr().err


def test_wif_workflow_is_manual_only_and_has_no_paid_query_path() -> None:
    path = ROOT / ".github/workflows/bigquery-source-parity.yml"
    workflow = path.read_text(encoding="utf-8")
    assert "\n  workflow_dispatch:" in workflow
    assert "\n  push:" not in workflow
    assert "\n  pull_request:" not in workflow
    assert "id-token: write" in workflow and "contents: read" in workflow
    assert "uses: google-github-actions/auth@v2" in workflow
    assert "GCP_WIF_PROVIDER" in workflow and "GCP_BIGQUERY_READONLY_SA" in workflow
    assert "workload_identity_provider:" in workflow and "service_account:" in workflow
    assert "--use-adc" in workflow
    assert "--max-source-rows 10000" in workflow
    assert "outputs/research/bigquery_direct_parity.json" in workflow
    assert "retention-days: 7" in workflow
    assert "bq query" not in workflow
    assert "dbt run" not in workflow
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in workflow
    assert "data/raw/" not in workflow
