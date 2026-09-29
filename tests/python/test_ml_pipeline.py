"""Smoke tests for the scoring layer on synthetic data (no Kaggle download needed)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ml = importlib.import_module("src.prepare_raw_and_ml")


def synthetic_frame(rows: int = 12_000, seed: int = 7) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=rows)
    X = pd.DataFrame(
        {
            "TransactionAmt": rng.gamma(2.0, 50.0, size=rows).astype("float32"),
            "signal": signal.astype("float32"),
            "noise": rng.normal(size=rows).astype("float32"),
            "channel": rng.integers(0, 4, size=rows).astype("int32"),
        }
    )
    y = pd.Series((signal + rng.normal(scale=0.7, size=rows) > 1.6).astype(int))
    transaction_dt = pd.Series(np.arange(rows) * 60)
    return X, y, transaction_dt


def test_encode_categoricals_maps_unseen_and_missing_values() -> None:
    train = pd.DataFrame({"card4": ["visa", "mastercard", None, "visa"]})
    test = pd.DataFrame({"card4": ["visa", "discover", None]})

    ml.encode_categoricals(train, test, ["card4"])

    assert train["card4"].dtype == "int32"
    assert train["card4"].iloc[0] == train["card4"].iloc[3]
    assert test["card4"].iloc[0] == train["card4"].iloc[0]
    assert test["card4"].iloc[1] == -1  # category never seen in train
    assert test["card4"].iloc[2] == train["card4"].iloc[2]  # missing keeps its own code


def test_fit_kwargs_is_off_by_default_and_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    assert ml.fit_kwargs(["channel"]) == {}

    monkeypatch.setattr(ml, "NATIVE_CATEGORICALS", True)
    assert ml.fit_kwargs(["channel"]) == {"categorical_feature": ["channel"]}
    assert ml.fit_kwargs([]) == {}


def test_model_ranks_synthetic_fraud_well() -> None:
    from sklearn.metrics import roc_auc_score

    X, y, _ = synthetic_frame()
    split = int(len(X) * 0.8)
    model = ml.lightgbm_model(n_estimators=60)
    model.fit(X.iloc[:split], y.iloc[:split])

    score = model.predict_proba(X.iloc[split:])[:, 1]
    assert roc_auc_score(y.iloc[split:], score) > 0.9


def test_native_categorical_fit_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ml, "NATIVE_CATEGORICALS", True)
    X, y, _ = synthetic_frame(rows=4_000)
    model = ml.lightgbm_model(n_estimators=20)
    model.fit(X, y, **ml.fit_kwargs(["channel"]))

    assert len(model.predict_proba(X)) == len(X)


def test_rolling_time_cv_returns_one_row_per_window() -> None:
    X, y, transaction_dt = synthetic_frame()

    metrics = ml.rolling_time_cv_metrics(X, y, transaction_dt, windows=2, categorical=["channel"])

    assert list(metrics["window_number"]) == [1, 2]
    assert {"roc_auc", "average_precision", "concept_drift_flag"} <= set(metrics.columns)
    assert (metrics["train_rows"] < len(X)).all()
    # expanding windows: training data grows and validation never overlaps it
    assert metrics["train_rows"].is_monotonic_increasing
    assert (metrics["validation_start_dt"] > 0).all()
    assert metrics["roc_auc"].between(0.5, 1.0).all()
