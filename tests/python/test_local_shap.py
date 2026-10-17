"""F05: only mathematically verified local SHAP can carry a local explanation label.

All tests are synthetic and offline. No cloud API, Kaggle data or private model
artifact is available in normal CI.
"""
from __future__ import annotations

import importlib
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import shap
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
store = importlib.import_module("src.local_shap")
web = importlib.import_module("webapp.main")
ml = importlib.import_module("src.prepare_raw_and_ml")
client = TestClient(web.app)


def verified_case(model_version: str | None = None, transaction_id: int = 321) -> dict:
    margin = 0.3 - 0.2 + 0.6
    result = store.build_local_shap_explanations(
        transaction_ids=[transaction_id],
        feature_names=["TransactionAmt", "V22"],
        shap_values=np.array([[-0.2, 0.6]]),
        expected_value=0.3,
        raw_margins=[margin],
        ranking_scores=[1 / (1 + math.exp(-margin))],
        model_version=model_version or web.MODEL_REGISTRY["model_version"],
    )
    return result[0]


def test_local_shap_tracks_signed_factors_and_margin_additivity() -> None:
    result = verified_case()
    assert result["method"] == "TreeSHAP"
    assert result["output_space"] == "LightGBM raw margin (log odds)"
    assert result["calibrated_probability"] is False
    assert result["label_source"] == "no_labels_in_explanation_artifact"
    assert result["raw_margin_additivity_residual"] == pytest.approx(0)
    assert result["raw_model_margin"] == pytest.approx(0.7)
    assert result["feature_count"] == 2
    assert result["factors"][0]["feature"] == "V22"
    assert result["factors"][0]["direction"] == "raises_model_score"
    assert result["factors"][1]["direction"] == "lowers_model_score"
    assert result["omitted_factor_sum"] == pytest.approx(0.0)
    assert "not a calibrated fraud probability" in result["methodology"].lower()


def test_binary_list_and_tensor_shapes_positive_class_are_supported() -> None:
    data = np.array([[0.25, -0.15]])
    raw = 0.4 + data.sum(axis=1)
    score = 1 / (1 + np.exp(-raw))
    common = {
        "transaction_ids": [1],
        "feature_names": ["a", "b"],
        "expected_value": [-0.4, 0.4],
        "raw_margins": raw,
        "ranking_scores": score,
        "model_version": "synthetic",
    }
    out_list = store.build_local_shap_explanations(
        shap_values=[-data, data], **common
    )[0]
    out_tensor = store.build_local_shap_explanations(
        shap_values=np.stack([-data, data], axis=2), **common
    )[0]
    assert out_list["raw_model_margin"] == pytest.approx(out_tensor["raw_model_margin"])
    assert out_list["factors"] == out_tensor["factors"]


@pytest.mark.parametrize(
    ("margins", "scores", "ids"),
    [
        ([0.9], [0.6], [321]),
        ([float("nan")], [0.6], [321]),
        ([0.7], [1.2], [321]),
        ([0.7], [0.67], [321, 321]),
    ],
)
def test_wrong_margin_score_and_duplicate_ids_are_refused(
    margins: list[float], scores: list[float], ids: list[int],
) -> None:
    with pytest.raises(ValueError):
        store.build_local_shap_explanations(
            transaction_ids=ids,
            feature_names=["a", "b"],
            shap_values=np.array([[-0.2, 0.6]]),
            expected_value=0.3,
            raw_margins=margins,
            ranking_scores=scores,
            model_version="test",
        )


def test_invalid_feature_names_or_nonfinite_shap_refused() -> None:
    with pytest.raises(ValueError):
        store.build_local_shap_explanations(
            transaction_ids=[1],
            feature_names=["a", "a"],
            shap_values=[[0.1, 0.2]],
            expected_value=0.3,
            raw_margins=[0.6],
            ranking_scores=[1 / (1 + np.exp(-0.6))],
            model_version="test",
        )
    with pytest.raises(ValueError):
        store.build_local_shap_explanations(
            transaction_ids=[1],
            feature_names=["a"],
            shap_values=[[np.nan]],
            expected_value=0.3,
            raw_margins=[0.6],
            ranking_scores=[0.65],
            model_version="test",
        )


def test_local_shap_from_real_synthetic_lightgbm_model_is_additive() -> None:
    rng = np.random.default_rng(5)
    n = 360
    signal = rng.normal(size=n)
    X = pd.DataFrame({
        "signal": signal,
        "noise": rng.normal(size=n),
        "V9": rng.normal(size=n),
    })
    y = (signal + rng.normal(size=n) * 0.6 > 0.4).astype(int)
    model = ml.lightgbm_model(n_estimators=20)
    model.fit(X.iloc[:290], y[:290])
    sample = X.iloc[290:300]
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(sample)
    cases = store.build_local_shap_explanations(
        transaction_ids=list(range(9001, 9011)),
        feature_names=list(sample.columns),
        shap_values=values,
        expected_value=explainer.expected_value,
        raw_margins=model.predict(sample, raw_score=True),
        ranking_scores=model.predict_proba(sample)[:, 1],
        model_version="synthetic-test-model",
    )
    assert len(cases) == 10
    assert max(abs(case["raw_margin_additivity_residual"]) for case in cases) < 1e-3


def test_private_sqlite_roundtrip_and_safe_replace(tmp_path: Path) -> None:
    dest = tmp_path / "local.sqlite"
    store.save_explanations(dest, [verified_case()])
    row = store.load_explanation(dest, 321)
    assert row is not None and row["model_version"] == web.MODEL_REGISTRY["model_version"]
    assert store.load_explanation(dest, 12345) is None
    before = dest.read_bytes()
    with pytest.raises(ValueError):
        store.save_explanations(dest, [{**verified_case(), "method": "heuristic"}])
    assert dest.read_bytes() == before
    assert list(tmp_path.glob(".local-shap-*.sqlite")) == []


def test_local_endpoint_is_internal_and_never_triggers_warehouse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    dest = tmp_path / "validated.sqlite"
    store.save_explanations(dest, [verified_case()])
    monkeypatch.setenv("WEB_INTERNAL_REFRESH_TOKEN", "internal-key-123")
    monkeypatch.setenv("WEB_LOCAL_SHAP_DB_PATH", str(dest))
    monkeypatch.setattr(web, "direct_aggregate", lambda *args: pytest.fail("warehouse queried"))
    monkeypatch.setattr(web, "run_query", lambda *args: pytest.fail("warehouse queried"))

    url = "/api/enterprise/cases/321/local-explanation"
    assert client.get(url).status_code == 403
    assert client.get(url, headers={"X-Internal-Refresh-Token": "wrong"}).status_code == 403
    good_headers = {"X-Internal-Refresh-Token": "internal-key-123"}
    response = client.get(url, headers=good_headers)
    assert response.status_code == 200
    assert response.json()["method"] == "TreeSHAP"
    assert client.get("/api/enterprise/cases/987/local-explanation", headers=good_headers).status_code == 404
    monkeypatch.setenv("WEB_LOCAL_SHAP_DB_PATH", str(tmp_path / "missing.sqlite"))
    assert client.get(url, headers=good_headers).status_code == 503


def test_local_endpoint_rejects_stale_model_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    dest = tmp_path / "wrong-version.sqlite"
    store.save_explanations(dest, [verified_case(model_version="wrong-model")])
    monkeypatch.setenv("WEB_INTERNAL_REFRESH_TOKEN", "secret")
    monkeypatch.setenv("WEB_LOCAL_SHAP_DB_PATH", str(dest))
    response = client.get(
        "/api/enterprise/cases/321/local-explanation",
        headers={"X-Internal-Refresh-Token": "secret"},
    )
    assert response.status_code == 503


def test_legacy_case_explain_is_explicitly_not_tree_shap() -> None:
    import inspect

    src = inspect.getsource(web.enterprise_case_explain)
    assert '"is_local_shap": False' in src
    assert '"explanation_type": "global_importance_heuristic"' in src
    assert '"calibrated_probability": False' in src
    assert "NOT local TreeSHAP" in src
