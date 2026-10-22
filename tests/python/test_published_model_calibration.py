"""Retrospective calibration safeguards; synthetic, offline, no training jobs."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import benchmark_published_model_calibration as study

ROOT = Path(__file__).resolve().parents[2]


def test_time_cuts_preserve_timestamp_groups_and_reject_unordered_times():
    times = np.repeat(np.arange(10, dtype=float), 3)
    cut = study.strict_cut(times, .55)
    assert times[:cut].max() < times[cut:].min()
    with pytest.raises(ValueError):
        study.strict_cut(times[::-1], .5)
    with pytest.raises(ValueError):
        study.strict_cut(np.ones(10), .5)


def test_core_only_v_selection_and_unknown_category_mapping():
    core = pd.DataFrame({"V1": [np.nan] * 5, "V2": [1.] * 5,
                         "ProductCD": ["A", "B", "A", "B", "A"]})
    later = pd.DataFrame({"V1": [4.], "V2": [np.nan], "ProductCD": ["new"]})
    matrices, selected = study.encode_core(core, [later], list(core))
    assert selected == ["V2", "ProductCD"]
    assert matrices[1].ProductCD.iloc[0] == -1
    assert np.isnan(matrices[1].V2.iloc[0])


def test_method_selection_uses_three_development_windows_and_stable_ties():
    folds = [{"metrics": {"platt": {"brier_score": .03}, "isotonic": {"brier_score": .02}}}] * 3
    assert study.select_method(folds) == "isotonic"
    with pytest.raises(ValueError):
        study.select_method(folds[:2])


def test_metrics_keep_review_queue_selection_label_blind_and_report_reliability():
    y = np.array([1, 0, 1, 0])
    report = study.metrics(y, np.array([.5, .5, .5, .5]))
    assert report["top_k_review_queue"]["top_1pct"]["fraud_cases_captured"] == 1
    assert sum(row["count"] for row in report["reliability_bins"]) == 4
    assert report["brier_score"] == .25
    assert report["roc_auc"] == .5
    with pytest.raises(ValueError):
        study.metrics(y, np.array([.5, .5, np.inf, .5]))


def test_relative_day_uncertainty_is_paired_and_deterministic():
    frame = pd.DataFrame({"isFraud": [0, 1, 0, 1, 0, 1],
                          "TransactionDT": np.arange(6) * 86400})
    selected, baseline = np.array([.1, .9] * 3), np.full(6, .5)
    report = study.day_block_uncertainty(frame, selected, baseline)
    assert report["percentile_95pct"][1] < 0
    assert report == study.day_block_uncertainty(frame, selected, baseline)


def test_standalone_notebook_matches_reviewed_implementation():
    path = ROOT / "scripts/benchmark_published_model_calibration.py"
    source = path.read_text(encoding="utf-8")
    notebook = json.loads((ROOT / "notebooks/published_model_calibration/published_model_calibration.ipynb").read_text())
    expected = ast.parse(source)
    expected.body = [node for node in expected.body
                     if not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
                     and not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                              and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__")]
    embedded = ast.parse("".join(notebook["cells"][1]["source"]))
    embedded.body = embedded.body[1:]  # source digest constant precedes exact implementation
    assert ast.dump(expected) == ast.dump(embedded)
    assert notebook["metadata"]["nexus"]["implementation_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), "calibration-notebook-cell", "exec")


def test_new_model_parameters_match_historical_family_except_thread_limit():
    legacy = ast.parse((ROOT / "src/prepare_raw_and_ml.py").read_text())
    function = next(node for node in legacy.body if isinstance(node, ast.FunctionDef) and node.name == "lightgbm_model")
    call = function.body[0].value
    legacy_values = {keyword.arg: ast.literal_eval(keyword.value) for keyword in call.keywords
                     if keyword.arg not in {"n_estimators", "n_jobs"}}
    assert {key: study.PARAMETERS[key] for key in legacy_values} == legacy_values
    assert study.PARAMETERS["n_estimators"] == 500
    assert study.PARAMETERS["n_jobs"] == 2
