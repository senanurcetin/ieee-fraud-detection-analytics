"""F04: experimental fraud score calibration with three disjoint temporal windows.

Core fit ~60% -> calibration ~20% -> untouched final holdout ~20%, with
timestamp ties kept together. Offline read-only DuckDB research only.
No model promotion, payments, BigQuery SQL, dbt writes or dashboard changes.

From repo root:
    python -m scripts.benchmark_temporal_calibration \
        --duckdb data/processed/ieee_fraud.duckdb \
        --output outputs/research/fraud_calibration.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import duckdb
import lightgbm
import numpy as np
import pandas as pd
import sklearn
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from scripts.benchmark_temporal_hygiene import DEFAULT_DUCKDB, read_local_features
from src import prepare_raw_and_ml as ml
from src.temporal_hygiene import FoldPreprocessor, chronological_holdout

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "research" / "fraud_calibration.json"


def temporal_three_way_split(
    transaction_dt: pd.Series,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """60/20/20 approximate row shares, time boundaries strictly nonoverlapping."""
    development, final_holdout = chronological_holdout(transaction_dt, train_fraction=0.8)
    core_local, calibration_local = chronological_holdout(
        transaction_dt.iloc[development].reset_index(drop=True),
        train_fraction=0.75,
    )
    core = development[core_local]
    calibration = development[calibration_local]
    times = pd.to_numeric(transaction_dt, errors="coerce").to_numpy(dtype="float64")
    if not (times[core].max() < times[calibration].min() < times[final_holdout].min()):
        raise AssertionError("Core, calibration and final holdout times overlap")
    return core, calibration, final_holdout


def calibration_metrics(
    labels: np.ndarray,
    scores: np.ndarray,
    bins: int = 10,
) -> dict[str, Any]:
    """Report reliability and ranking; ECE bins are fixed *a priori*."""
    y = np.asarray(labels)
    p = np.asarray(scores, dtype="float64")
    if y.ndim != 1 or p.ndim != 1 or y.size != p.size or not y.size:
        raise ValueError("Scores and labels must be nonempty aligned 1D vectors")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("Require binary labels and finite scores between 0 and 1")
    if bins < 2:
        raise ValueError("At least two ECE bins required")
    reliability = []
    ece = 0.0
    for bucket in range(bins):
        low, high = bucket / bins, (bucket + 1) / bins
        selected = (p >= low) & (p < high if bucket < bins - 1 else p <= high)
        n = int(selected.sum())
        if n:
            confidence = float(p[selected].mean())
            observed = float(y[selected].mean())
            ece += n / len(y) * abs(confidence - observed)
            reliability.append({
                "bin": bucket,
                "count": n,
                "mean_score": confidence,
                "observed_rate": observed,
            })
    return {
        "rows": int(len(y)),
        "fraud_count": int(y.sum()),
        "fraud_rate": float(y.mean()),
        "mean_score": float(p.mean()),
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "average_precision": (
            float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else None
        ),
        "brier_score": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "expected_calibration_error": float(ece),
        "reliability_bins": reliability,
    }


def benchmark_calibration(
    data: pd.DataFrame,
    feature_cols: list[str],
    categorical: list[str],
    n_estimators: int = 150,
    native_categorical: bool = False,
    v_missingness_threshold: float = 0.95,
) -> dict[str, Any]:
    """Train model on core, learn calibrators on middle, evaluate final only."""
    if n_estimators < 1 or not 0 <= v_missingness_threshold <= 1:
        raise ValueError("Invalid modeling settings")
    required = {"isFraud", "TransactionDT", *feature_cols}
    if not required.issubset(data.columns) or "isFraud" in feature_cols:
        raise ValueError("Missing predictors or label mistakenly included in predictors")
    y_all = pd.to_numeric(data["isFraud"], errors="coerce")
    if y_all.isna().any() or not y_all.isin([0, 1]).all():
        raise ValueError("Invalid fraud labels")
    core_ix, calibrate_ix, final_ix = temporal_three_way_split(data["TransactionDT"])
    core = data.iloc[core_ix].copy()
    calibration = data.iloc[calibrate_ix].copy()
    final = data.iloc[final_ix].copy()
    for label, frame in [("core", core), ("calibration", calibration), ("final_holdout", final)]:
        if frame["isFraud"].nunique() != 2:
            raise ValueError(f"{label} period must have both binary classes")
    prep = FoldPreprocessor(tuple(categorical), v_missingness_threshold=v_missingness_threshold)
    X_core = prep.fit_transform(core[feature_cols])
    X_cal = prep.transform(calibration[feature_cols])
    X_final = prep.transform(final[feature_cols])

    model = ml.lightgbm_model(n_estimators=n_estimators)
    kwargs = {"categorical_feature": prep.categorical_} if native_categorical and prep.categorical_ else {}
    model.fit(X_core, core["isFraud"].astype(int), **kwargs)
    calibrate_scores = model.predict_proba(X_cal)[:, 1]
    final_raw = model.predict_proba(X_final)[:, 1]
    calibrate_labels = calibration["isFraud"].astype(int).to_numpy()
    final_labels = final["isFraud"].astype(int).to_numpy()

    platt = LogisticRegression(max_iter=1000, random_state=42)
    platt.fit(calibrate_scores.reshape(-1, 1), calibrate_labels)
    final_platt = platt.predict_proba(final_raw.reshape(-1, 1))[:, 1]

    isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
    isotonic.fit(calibrate_scores, calibrate_labels)
    final_iso = isotonic.predict(final_raw)

    # Baseline is an earlier core-only prior; no final holdout prevalence leaks.
    core_rate = float(core["isFraud"].mean())
    methods = {
        "raw_ranker": final_raw,
        "platt_logistic": final_platt,
        "isotonic": final_iso,
        "constant_core_prior": np.full(len(final), core_rate, dtype="float64"),
    }
    metrics = {key: calibration_metrics(final_labels, value) for key, value in methods.items()}
    fingerprint_columns = [
        col for col in ("TransactionID", "TransactionDT", "isFraud") if col in data
    ]
    fingerprint = hashlib.sha256(
        data[fingerprint_columns].to_csv(index=False).encode("utf-8")
    ).hexdigest()
    return {
        "study": "IEEE-CIS disjoint temporal model score calibration experiment",
        "experimental_only": True,
        "changes_published_model": False,
        "input_rows": len(data),
        "source_rows_identity_time_label_sha256": fingerprint,
        "split_rows": {
            "core_model_fit": len(core),
            "calibration_only": len(calibration),
            "untouched_final_holdout": len(final),
        },
        "strict_time_boundaries": {
            "core_max": float(core["TransactionDT"].max()),
            "calibration_min": float(calibration["TransactionDT"].min()),
            "calibration_max": float(calibration["TransactionDT"].max()),
            "holdout_min": float(final["TransactionDT"].min()),
        },
        "core_fraud_rate": core_rate,
        "calibration_fraud_rate": float(calibration["isFraud"].mean()),
        "calibration_positive_count": int(calibrate_labels.sum()),
        "feature_count_fit_only": len(prep.feature_names_),
        "categorical_feature_count_fit_only": len(prep.categorical_),
        "native_categorical": bool(native_categorical),
        "estimators_per_fit": n_estimators,
        "final_holdout_metrics": metrics,
        "calibration_methods_fit_window": "middle_only",
        "holdout_labels_used_for_fitting": False,
        "interpretation_limits": [
            "All calibrators are experimental and evaluated on an untouched later period.",
            "Model is not deployed; holdout metrics are not published or live-payment benchmarks.",
            "Raw class-weighted scores are ranking scores until independent calibration is accepted.",
            "Isotonic regression may overfit sparse calibration positives or harm discrimination via score ties.",
            "Do not select a model solely on these final holdout results; reserve a future external test.",
        ],
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "lightgbm": lightgbm.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb", type=Path, default=DEFAULT_DUCKDB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--n-estimators", type=int, default=150)
    parser.add_argument("--native-categorical", action="store_true")
    parser.add_argument("--max-rows", type=int, default=0, help="Subset smoke test, not full-data evidence")
    parser.add_argument("--v-missingness-threshold", type=float, default=0.95)
    args = parser.parse_args(argv)
    if args.n_estimators < 1 or args.max_rows < 0 or not 0 <= args.v_missingness_threshold <= 1:
        parser.error("Invalid experiment options")
    try:
        frame, features, categorical = read_local_features(args.duckdb, args.max_rows)
        report = benchmark_calibration(
            frame, features, categorical, args.n_estimators,
            args.native_categorical, args.v_missingness_threshold,
        )
    except (ValueError, FileNotFoundError, duckdb.Error) as exc:
        # Never echo source paths or credential content.
        print(f"Calibration experiment unavailable: {type(exc).__name__}")
        return 2
    report["subset_mode"] = bool(args.max_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Experimental calibration report written locally; no model has been promoted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
