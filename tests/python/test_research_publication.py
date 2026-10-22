"""Public research contracts: aggregate-only, no cloud access, fail closed."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from webapp import research_evidence as research
from webapp.main import app


@pytest.fixture
def report():
    metric = {
        "rows": 10, "fraud_count": 2, "fraud_rate": 0.2,
        "roc_auc": 0.8, "average_precision": 0.6, "brier_score": 0.1,
        "log_loss": 0.3, "expected_calibration_error": 0.03,
        "reliability_bins": [{"bin": 0, "count": 10, "mean_score": 0.2, "observed_rate": 0.2}],
    }
    metrics = {method: copy.deepcopy(metric) for method in research.METHODS}
    windows = {"core": {"rows": 100, "min_transaction_dt": 0, "max_transaction_dt": 5},
               "calibration": {"rows": 10, "min_transaction_dt": 6, "max_transaction_dt": 10},
               "validation": {"rows": 10, "fraud_count": 2, "min_transaction_dt": 11, "max_transaction_dt": 15}}
    final_windows = copy.deepcopy(windows)
    final_windows["core"]["rows"] = 590520
    final_windows["validation"].update(min_transaction_dt=21, max_transaction_dt=30)
    return {
        "schema_version": 1, "model_version": "synthetic-research-test",
        "source": {"rows": 590540, "subset_mode": False,
                   "transaction_sha256": "a" * 64, "identity_sha256": "b" * 64,
                   "ordered_rows_sha256": "c" * 64},
        "development": {"selected_method": "platt", "folds": [
            {"metrics": copy.deepcopy(metrics), "windows": copy.deepcopy(windows)} for _ in range(3)
        ]},
        "final": {"selected_method": "platt", "metrics": metrics, "windows": final_windows,
                  "acceptance": {"accepted_for_retrospective_probability": True}},
        "score_contract": {"not_for_live_decisions": True},
        "limitations": ["Synthetic test fixture only; never published as measured evidence."],
    }


def test_aggregate_endpoint_retains_model_identity_and_file_digest(report, tmp_path, monkeypatch):
    path = tmp_path / "research.json"
    raw = json.dumps(report).encode()
    path.write_bytes(raw)
    monkeypatch.setattr(research, "CALIBRATION_PATH", path)
    with TestClient(app) as client:
        response = client.get("/api/research/calibration")
    assert response.status_code == 200
    assert response.json() == {"artifact_sha256": hashlib.sha256(raw).hexdigest(), "evidence": report}


def test_removed_or_damaged_evidence_is_not_served_from_cache(report, tmp_path, monkeypatch):
    path = tmp_path / "research.json"
    path.write_text(json.dumps(report))
    monkeypatch.setattr(research, "CALIBRATION_PATH", path)
    with TestClient(app) as client:
        assert client.get("/api/research/calibration").status_code == 200
        path.unlink()
        assert client.get("/api/research/calibration").status_code == 503
        path.write_text('{"private_key": "mock-secret-never-publish"}')
        response = client.get("/api/research/calibration")
        assert response.status_code == 503
        assert "mock-secret" not in response.text


@pytest.mark.parametrize("damage", ["subset", "selection", "nonfinite", "raw_records", "missing_fold", "shape", "overlap", "bin_support"])
def test_incomplete_or_unsafe_evidence_is_rejected(report, damage):
    if damage == "subset":
        report["source"]["subset_mode"] = True
    elif damage == "selection":
        report["final"]["selected_method"] = "isotonic"
    elif damage == "nonfinite":
        report["final"]["metrics"]["raw"]["brier_score"] = float("nan")
    elif damage == "raw_records":
        report["transactions"] = [{"transaction_id": 123}]
    elif damage == "missing_fold":
        report["development"]["folds"].pop()
    elif damage == "overlap":
        report["final"]["windows"]["calibration"]["max_transaction_dt"] = 21
    elif damage == "bin_support":
        report["final"]["metrics"]["platt"]["reliability_bins"][0]["count"] = 9
    else:
        report["final"] = []
    with pytest.raises(ValueError):
        research.validate_calibration_report(report)


def test_rejected_probability_candidate_remains_publishable_research(report):
    report["final"]["acceptance"]["accepted_for_retrospective_probability"] = False
    assert research.validate_calibration_report(report)["final"]["acceptance"] == {
        "accepted_for_retrospective_probability": False,
    }


def test_research_page_discloses_old_model_and_new_research_separation():
    with TestClient(app) as client:
        response = client.get("/research")
    assert response.status_code == 200
    assert "historical v2 model remains an uncalibrated ranking model" in response.text
    assert "must not be applied to the old dashboard scores" in response.text
    assert "/static/seo/favicon.svg" in response.text


def test_committed_full_source_calibration_is_bound_to_reproducible_implementation():
    envelope = research.load_calibration_report()
    report = envelope["evidence"]
    root = Path(__file__).resolve().parents[2]
    implementation = (root / "scripts/benchmark_published_model_calibration.py").read_text(encoding="utf-8")
    assert report["implementation_sha256"] == hashlib.sha256(implementation.encode()).hexdigest()
    assert report["base_model_contract"]["hyperparameters"]["n_estimators"] == 500
    assert report["score_contract"]["historical_v2_mapping"] is False
    selected = report["development"]["selected_method"]
    assert report["final"]["metrics"][selected]["brier_score"] < report["final"]["metrics"]["constant"]["brier_score"]
    assert report["final"]["uncertainty"]["percentile_95pct"][1] < 0


def test_committed_source_audit_is_bound_to_current_snapshot_queries_and_verifier():
    envelope = research.load_source_parity_report()
    report = envelope["evidence"]
    root = Path(__file__).resolve().parents[2]
    implementation = (root / "scripts/verify_reporting_full_parity_readonly.py").read_text(encoding="utf-8")
    assert report["verifier_source_sha256"] == hashlib.sha256(implementation.encode()).hexdigest()
    assert report["verified_full_27_group_parity"] is True
    assert report["fact_selected_rows_read"] == 590540
    assert report["raw_source_records_written"] is False


def test_source_audit_does_not_survive_a_snapshot_or_query_change(tmp_path, monkeypatch):
    original = research.load_source_parity_report()["evidence"]
    path = tmp_path / "source-parity.json"
    damaged = copy.deepcopy(original)
    damaged["snapshot_canonical_sha256"] = "0" * 64
    path.write_text(json.dumps(damaged))
    monkeypatch.setattr(research, "SOURCE_PARITY_PATH", path)
    with pytest.raises(ValueError, match="different snapshot"):
        research.load_source_parity_report()
    damaged = copy.deepcopy(original)
    damaged["groups"]["niche_drilldown"]["query_sha256"] = "0" * 64
    path.write_text(json.dumps(damaged))
    with pytest.raises(ValueError, match="query changed"):
        research.load_source_parity_report()
