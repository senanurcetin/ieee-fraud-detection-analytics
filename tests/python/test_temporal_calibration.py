"""F04: synthetic calibration window and metric contracts; no real dataset required."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
calibration = importlib.import_module("scripts.benchmark_temporal_calibration")


def synthetic(rows: int = 520, seed: int = 43) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    signal = rng.normal(size=rows)
    y = (signal + rng.normal(scale=1.2, size=rows) > 0.45).astype(int)
    return pd.DataFrame({
        "TransactionID": np.arange(rows) + 300_000,
        "TransactionDT": np.arange(rows) * 60,
        "isFraud": y,
        "signal": signal.astype("float32"),
        "amount": rng.gamma(2, 40, size=rows).astype("float32"),
        "card4": np.where(np.arange(rows) < rows * 0.60, "visa", "later_category"),
        "V1": rng.normal(size=rows).astype("float32"),
        "V2": np.concatenate(([np.nan] * (rows // 2), np.ones(rows - rows // 2))),
    })


def test_temporal_three_way_split_never_shares_time() -> None:
    df = synthetic()
    core, middle, last = calibration.temporal_three_way_split(df["TransactionDT"])
    assert set(core).isdisjoint(middle)
    assert set(core).isdisjoint(last)
    assert set(middle).isdisjoint(last)
    assert len(core) + len(middle) + len(last) == len(df)
    assert df["TransactionDT"].iloc[core].max() < df["TransactionDT"].iloc[middle].min()
    assert df["TransactionDT"].iloc[middle].max() < df["TransactionDT"].iloc[last].min()


def test_three_way_split_holds_tied_timestamps_together() -> None:
    times = pd.Series(np.repeat(np.arange(50), 4))
    a, b, c = calibration.temporal_three_way_split(times)
    for left, right in ((a, b), (b, c)):
        assert times.iloc[left].max() < times.iloc[right].min()
    assert len(a) + len(b) + len(c) == len(times)


def test_calibration_metrics_is_properly_weighted() -> None:
    y = np.array([0, 0, 1, 1])
    score = np.array([0.10, 0.20, 0.70, 0.95])
    result = calibration.calibration_metrics(y, score, bins=10)
    assert result["rows"] == 4
    assert result["fraud_count"] == 2
    assert result["mean_score"] == pytest.approx(score.mean())
    assert result["roc_auc"] == pytest.approx(1.0)
    assert result["average_precision"] == pytest.approx(1.0)
    assert result["brier_score"] == pytest.approx(np.mean((y - score) ** 2))
    assert result["expected_calibration_error"] == pytest.approx(np.abs(score-y).mean())
    assert sum(bin_row["count"] for bin_row in result["reliability_bins"]) == 4


@pytest.mark.parametrize(
    ("labels", "scores"),
    (([0, 1], [0.2]), ([0, 1], [0.2, 1.1]), ([0, 2], [0.2, 0.8]), ([], [])),
)
def test_bad_calibration_score_contract_raises(labels: list[int], scores: list[float]) -> None:
    with pytest.raises(ValueError):
        calibration.calibration_metrics(np.array(labels), np.array(scores))


def test_compare_raw_platt_isotonic_and_core_baseline_on_final_holdout() -> None:
    data = synthetic()
    result = calibration.benchmark_calibration(
        data,
        ["TransactionDT", "signal", "amount", "card4", "V1", "V2"],
        ["card4"],
        n_estimators=15,
        native_categorical=True,
        v_missingness_threshold=0.70,
    )
    assert result["experimental_only"]
    assert result["changes_published_model"] is False
    assert result["calibration_methods_fit_window"] == "middle_only"
    assert result["holdout_labels_used_for_fitting"] is False
    assert sum(result["split_rows"].values()) == len(data)
    assert result["feature_count_fit_only"] == 5  # V2 excluded from the core fit window
    assert result["native_categorical"] is True
    assert result["calibration_positive_count"] > 0
    t = result["strict_time_boundaries"]
    assert t["core_max"] < t["calibration_min"]
    assert t["calibration_max"] < t["holdout_min"]
    methods = result["final_holdout_metrics"]
    assert set(methods) == {
        "raw_ranker", "platt_logistic", "isotonic", "constant_core_prior"
    }
    for values in methods.values():
        assert values["rows"] == result["split_rows"]["untouched_final_holdout"]
        assert 0 <= values["brier_score"] <= 1
        assert 0 <= values["expected_calibration_error"] <= 1
    assert methods["constant_core_prior"]["mean_score"] == pytest.approx(result["core_fraud_rate"])
    assert len(result["source_rows_identity_time_label_sha256"]) == 64


def test_calibration_rejects_one_class_fit_or_disjoint_periods() -> None:
    data = synthetic(100)
    data.loc[data["TransactionDT"] >= 60 * 60, "isFraud"] = 0
    with pytest.raises(ValueError, match="both binary classes"):
        calibration.benchmark_calibration(data, ["signal"], [], n_estimators=10)


def test_calibration_script_never_updates_existing_dashboard() -> None:
    source = (ROOT / "scripts" / "benchmark_temporal_calibration.py").read_text(encoding="utf-8")
    assert "read_local_features" in source
    assert "model_registry.json" not in source
    assert "build_web_snapshot" not in source
    assert "create or replace" not in source.lower()
    assert "BigQuery" not in source.split("def main", maxsplit=1)[1]
