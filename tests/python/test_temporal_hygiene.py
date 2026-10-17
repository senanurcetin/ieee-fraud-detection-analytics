"""F03 guards: train-only preprocessing, disjoint time folds and local model comparisons.

Synthetic records only; no Kaggle, BigQuery, dbt, model registry or dashboard writes.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
hygiene = importlib.import_module("src.temporal_hygiene")
research = importlib.import_module("scripts.benchmark_temporal_hygiene")


def synthetic(rows: int = 260, seed: int = 41) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=rows)
    labels = (signal + rng.normal(scale=0.8, size=rows) > 0.45).astype(int)
    return pd.DataFrame({
        "TransactionID": np.arange(310_000, 310_000 + rows),
        "TransactionDT": np.arange(rows) * 60,
        "isFraud": labels,
        "signal": signal.astype("float32"),
        "noise": rng.normal(size=rows).astype("float32"),
        "card4": np.where(np.arange(rows) < rows * 0.8, "visa", "future_only"),
        "V1": rng.normal(size=rows).astype("float32"),
        "V2": [np.nan] * (rows // 2) + [1.0] * (rows - rows // 2),
    })


def test_strict_holdout_never_splits_same_transaction_dt() -> None:
    times = pd.Series([20, 10, 30, 30, 30, 40, 50, 60, 70, 80])
    fit, holdout = hygiene.chronological_holdout(times, train_fraction=0.4)
    assert set(fit).isdisjoint(holdout)
    assert times.iloc[fit].max() < times.iloc[holdout].min()
    assert {i for i in [2, 3, 4] if i in set(fit)} in (set(), {2, 3, 4})


@pytest.mark.parametrize("values", ([1, 1, 1, 1], [1, None, 3, 4], [1, 2, float("inf"), 4]))
def test_strict_holdout_rejects_ambiguous_time(values: list[float]) -> None:
    with pytest.raises(ValueError):
        hygiene.chronological_holdout(pd.Series(values))


def test_holdout_rejects_bad_fraction() -> None:
    with pytest.raises(ValueError):
        hygiene.chronological_holdout(pd.Series([1, 2, 3, 4]), 1)


def test_cv_folds_never_overlap_timestamps_or_final_holdout() -> None:
    data = synthetic(280)
    fit, holdout = hygiene.chronological_holdout(data["TransactionDT"])
    development = data.iloc[fit].reset_index(drop=True)
    validation = data.iloc[holdout]
    folds = hygiene.expanding_time_splits(development["TransactionDT"], windows=3, min_train_rows=40)
    assert len(folds) == 3
    prev_train = 0
    prev_valid = set()
    for train_index, valid_index in folds:
        assert len(train_index) > prev_train
        assert set(train_index).isdisjoint(valid_index)
        assert set(valid_index).isdisjoint(prev_valid)
        assert development["TransactionDT"].iloc[train_index].max() < (
            development["TransactionDT"].iloc[valid_index].min()
        )
        assert development["TransactionDT"].iloc[valid_index].max() < validation["TransactionDT"].min()
        prev_train = len(train_index)
        prev_valid.update(valid_index)


def test_cv_tie_boundary_is_strict_and_deterministic() -> None:
    times = pd.Series(np.repeat(np.arange(30), 3))
    folds = hygiene.expanding_time_splits(times, windows=3, min_train_rows=12)
    assert len(folds) == 3
    for a, b in folds:
        assert times.iloc[a].max() < times.iloc[b].min()
        assert set(a).isdisjoint(b)


def test_fit_only_encoding_rejects_unknown_future_categories() -> None:
    fit = pd.DataFrame({"card4": ["visa", "mastercard", None, "visa"], "amount": [1, 2, 3, 4]})
    future = pd.DataFrame({"card4": ["visa", "discover", None], "amount": [5, 6, 7]})
    transform = hygiene.FoldPreprocessor(("card4",)).fit(fit)
    old = transform.transform(fit)
    new = transform.transform(future)
    assert new["card4"].iloc[0] == old["card4"].iloc[0]
    assert new["card4"].iloc[1] == -1
    assert new["card4"].iloc[2] == -1
    assert transform.category_maps_["card4"] == {"mastercard": 0, "visa": 1}
    assert fit["card4"].iloc[2] is None
    assert future["card4"].iloc[1] == "discover"


def test_future_missingness_never_changes_fit_only_vesta_selection() -> None:
    fit = pd.DataFrame({
        "V1": [np.nan, np.nan, np.nan, 5.0],
        "V2": [1.0, 2.0, 3.0, 4.0],
        "card4": ["visa"] * 4,
    })
    future = pd.DataFrame({
        "V1": [10.0] * 4,
        "V2": [np.nan] * 4,
        "card4": ["unseen"] * 4,
    })
    prep = hygiene.FoldPreprocessor(("card4",), v_missingness_threshold=0.5).fit(fit)
    assert prep.feature_names_ == ["V2", "card4"]
    assert prep.v_missingness_ == {"V1": 0.75, "V2": 0.0}
    mapped = prep.transform(future)
    assert "V1" not in mapped
    assert mapped["V2"].isna().all()
    assert (mapped["card4"] == -1).all()


def test_score_bands_depend_only_on_fit_predictions() -> None:
    fit_scores = np.linspace(0.01, 0.99, 101)
    holdout_scores = np.full(20, 1.0)
    boundaries = hygiene.training_risk_band_edges(fit_scores)
    assert boundaries["high_p95"] == pytest.approx(np.quantile(fit_scores, 0.95))
    assert boundaries == hygiene.training_risk_band_edges(fit_scores.copy())
    assert boundaries["high_p95"] < np.quantile(np.concatenate((fit_scores, holdout_scores)), 0.95)


@pytest.mark.parametrize("bad", ([], [np.nan], [-0.1], [1.1]))
def test_score_bands_reject_invalid_fit_scores(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        hygiene.training_risk_band_edges(np.asarray(bad))


def test_benchmark_compares_two_fair_native_modes_without_holdout_leakage() -> None:
    data = synthetic(260)
    result = research.benchmark(
        data,
        feature_cols=["TransactionDT", "signal", "noise", "card4", "V1", "V2"],
        categorical=["card4"],
        n_estimators=12,
        windows=2,
        min_train_rows=40,
        v_missingness_threshold=0.70,
    )
    assert result["experimental_only"] is True
    assert result["changes_published_model"] is False
    assert result["holdout_strictly_later"] is True
    assert result["folds_derived_from_development_only"] is True
    assert result["usable_cv_windows"] == 2
    assert len(result["input_identity_time_label_sha256"]) == 64
    assert set(result["models"]) == {"ordinal_numeric", "lightgbm_native_categorical"}
    for arm in result["models"].values():
        holdout = arm["final_holdout"]
        assert holdout["train_max_transaction_dt"] < holdout["holdout_min_transaction_dt"]
        assert holdout["rows"] == result["holdout_validation_rows"]
        assert 0 <= holdout["fit_p95_review_workload"] <= 1
        assert holdout["unknown_or_missing_holdout_codes"]["card4"] > 0
        assert len(arm["development_folds"]) == 2
        for fold in arm["development_folds"]:
            assert fold["train_max_transaction_dt"] < fold["holdout_min_transaction_dt"]


def test_invalid_experiment_labels_or_target_predictor_rejected() -> None:
    data = synthetic(80)
    with pytest.raises(ValueError):
        research.benchmark(data, ["isFraud", "signal"], [], windows=0, n_estimators=2)
    data["isFraud"] = 0
    with pytest.raises(ValueError):
        research.benchmark(data, ["signal"], [], windows=0, n_estimators=2)


def test_experiment_is_non_destructive_to_published_registry() -> None:
    source = (ROOT / "scripts" / "benchmark_temporal_hygiene.py").read_text(encoding="utf-8")
    assert "read_only=True" in source
    assert "create or replace table" not in source.lower()
    assert "model_registry.json" not in source
    assert "build_web_snapshot" not in source
