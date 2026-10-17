"""Compare strictly chronological IEEE-CIS modeling on an existing local DuckDB.

EXPERIMENTAL, not a new published model. No Kaggle download, GCP access, dbt
writes, dashboard refresh, DuckDB mutation or altered model registry.

Usage (from repository root):
  python -m scripts.benchmark_temporal_hygiene \
      --duckdb data/processed/ieee_fraud.duckdb \
      --output outputs/research/fraud_temporal_hygiene.json
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
from sklearn.metrics import average_precision_score, roc_auc_score

from src import prepare_raw_and_ml as ml
from src.temporal_hygiene import (
    FoldPreprocessor,
    chronological_holdout,
    expanding_time_splits,
    training_risk_band_edges,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DUCKDB = ROOT / "data" / "processed" / "ieee_fraud.duckdb"
DEFAULT_OUTPUT = ROOT / "outputs" / "research" / "fraud_temporal_hygiene.json"


def metrics(y: pd.Series, scores: np.ndarray, p95_fit: float) -> dict[str, Any]:
    """Evaluate a predeclared fit-derived queue cutoff on held-out labels."""
    actual = y.to_numpy(dtype="int8")
    if len(actual) != len(scores) or not len(actual) or not np.isfinite(scores).all():
        raise ValueError("Predictions and labels must be finite, nonempty, and aligned")
    selected = np.asarray(scores) >= p95_fit
    fraud_count = int(actual.sum())
    captured = int(actual[selected].sum())
    return {
        "rows": int(len(actual)),
        "fraud_cases": fraud_count,
        "fraud_rate": float(actual.mean()),
        "roc_auc": float(roc_auc_score(actual, scores)) if len(np.unique(actual)) == 2 else None,
        "average_precision": (
            float(average_precision_score(actual, scores)) if len(np.unique(actual)) == 2 else None
        ),
        "fit_p95_review_workload": float(selected.mean()),
        "fit_p95_review_precision": float(captured / selected.sum()) if selected.any() else None,
        "fit_p95_fraud_capture": float(captured / fraud_count) if fraud_count else None,
    }


def _fit_and_score(
    development: pd.DataFrame,
    validation: pd.DataFrame,
    feature_cols: list[str],
    categorical: list[str],
    n_estimators: int,
    native: bool,
    missingness: float,
) -> tuple[dict[str, Any], FoldPreprocessor]:
    encoder = FoldPreprocessor(tuple(categorical), v_missingness_threshold=missingness)
    fit_features = encoder.fit_transform(development[feature_cols])
    hold_features = encoder.transform(validation[feature_cols])
    model = ml.lightgbm_model(n_estimators=n_estimators)
    kwargs = {"categorical_feature": encoder.categorical_} if native and encoder.categorical_ else {}
    model.fit(fit_features, development["isFraud"].astype(int), **kwargs)
    hold_scores = model.predict_proba(hold_features)[:, 1]
    fit_scores = model.predict_proba(fit_features)[:, 1]
    edges = training_risk_band_edges(fit_scores)
    result = metrics(validation["isFraud"], hold_scores, edges["high_p95"])
    result["fit_score_quantiles"] = edges
    result["feature_count"] = len(encoder.feature_names_)
    result["v_features_selected"] = sum(
        name.startswith("V") and name[1:].isdigit() for name in encoder.feature_names_
    )
    result["categorical_feature_count"] = len(encoder.categorical_)
    result["unknown_or_missing_holdout_codes"] = {
        name: int((hold_features[name] == -1).sum()) for name in encoder.categorical_
    }
    result["train_max_transaction_dt"] = float(development["TransactionDT"].max())
    result["holdout_min_transaction_dt"] = float(validation["TransactionDT"].min())
    if result["train_max_transaction_dt"] >= result["holdout_min_transaction_dt"]:
        raise AssertionError("Temporal boundary is contaminated")
    return result, encoder


def benchmark(
    data: pd.DataFrame,
    feature_cols: list[str],
    categorical: list[str],
    n_estimators: int = 150,
    windows: int = 3,
    min_train_rows: int = 10_000,
    v_missingness_threshold: float = 0.95,
) -> dict[str, Any]:
    """Both arms get identical temporal rows and fold-local preprocessing."""
    required = {"isFraud", "TransactionDT", *feature_cols}
    if not required.issubset(data.columns) or "isFraud" in feature_cols:
        raise ValueError("Missing required columns or label is in the predictors")
    if n_estimators < 1 or windows < 0 or min_train_rows < 1:
        raise ValueError("Invalid estimator/window settings")
    y = pd.to_numeric(data["isFraud"], errors="coerce")
    if y.isna().any() or not y.isin([0, 1]).all() or y.nunique() != 2:
        raise ValueError("Binary fraud labels with both classes are required")
    fit_indices, holdout_indices = chronological_holdout(data["TransactionDT"])
    development = data.iloc[fit_indices].copy().reset_index(drop=True)
    holdout = data.iloc[holdout_indices].copy().reset_index(drop=True)
    if development["isFraud"].nunique() != 2 or holdout["isFraud"].nunique() != 2:
        raise ValueError("Both classes are needed in train and final holdout")

    # Development folds never include the final holdout. Each fold fits its own
    # categorical vocabulary and missingness filter from that fold's fit rows.
    folds = expanding_time_splits(
        development["TransactionDT"],
        windows=max(windows, 1),
        min_train_rows=min_train_rows,
    ) if windows else []

    results: dict[str, Any] = {}
    for label, native in [("ordinal_numeric", False), ("lightgbm_native_categorical", True)]:
        holdout_metrics, _ = _fit_and_score(
            development,
            holdout,
            feature_cols,
            categorical,
            n_estimators,
            native,
            v_missingness_threshold,
        )
        fold_records = []
        for number, (train_index, valid_index) in enumerate(folds, start=1):
            frame_fit = development.iloc[train_index]
            frame_valid = development.iloc[valid_index]
            if frame_fit["isFraud"].nunique() != 2 or frame_valid["isFraud"].nunique() != 2:
                fold_records.append({
                    "fold": number,
                    "status": "SKIPPED_ONE_CLASS",
                    "train_rows": len(train_index),
                    "validation_rows": len(valid_index),
                })
                continue
            fold_metrics, _ = _fit_and_score(
                frame_fit,
                frame_valid,
                feature_cols,
                categorical,
                n_estimators,
                native,
                v_missingness_threshold,
            )
            fold_metrics["fold"] = number
            fold_metrics["status"] = "EVALUATED"
            fold_records.append(fold_metrics)
        results[label] = {"final_holdout": holdout_metrics, "development_folds": fold_records}

    identity_fields = [field for field in ["TransactionID", "TransactionDT", "isFraud"] if field in data]
    # Fingerprint identity/time/labels without publishing row-level observations.
    digest = hashlib.sha256(
        data[identity_fields].to_csv(index=False).encode("utf-8")
    ).hexdigest()
    return {
        "study": "IEEE-CIS fit-window-only categorical and V feature hygiene comparison",
        "study_version": 1,
        "experimental_only": True,
        "changes_published_model": False,
        "input_rows": int(len(data)),
        "input_identity_time_label_sha256": digest,
        "holdout_fit_rows": len(development),
        "holdout_validation_rows": len(holdout),
        "holdout_strictly_later": True,
        "folds_derived_from_development_only": True,
        "requested_cv_windows": windows,
        "usable_cv_windows": len(folds),
        "fit_only_v_missingness_threshold": v_missingness_threshold,
        "estimators_per_fit": n_estimators,
        "models": results,
        "cautions": [
            "Scores from class-weighted LightGBM are ranking scores, not calibrated fraud probabilities.",
            "No random-split experiment is implied; chronological evaluation is the only comparison here.",
            "Score quantile thresholds are learned on the fit window; final holdout labels are not used to set them.",
            "No model promotion or historical dashboard metrics changes occur from this report.",
        ],
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "lightgbm": lightgbm.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }


def read_local_features(db_path: Path, max_rows: int = 0) -> tuple[pd.DataFrame, list[str], list[str]]:
    if not db_path.is_file():
        raise FileNotFoundError("Local source DuckDB not found")
    if max_rows < 0:
        raise ValueError("max_rows cannot be negative")
    with duckdb.connect(str(db_path), read_only=True) as con:
        # Use project feature selection to discover its categorical/numeric
        # definitions, but add back *all* existing V columns before training.
        # The model then selects V features solely from fit-window missingness.
        features, _, categorical = ml.available_feature_columns(con)
        txn_cols = ml.table_columns(con, "raw.train_transaction")
        all_v = [f"V{i}" for i in range(1, 340) if f"V{i}" in txn_cols]
        features = list(dict.fromkeys(features + all_v))
        # Stable TransactionID tie-break makes original-row ordering and
        # source identity/time/label fingerprints identical across runs.
        # The historic publishing pipeline retains its old default SQL.
        frame = con.execute(ml.feature_query("train", features, stable_ties=True)).fetch_df()
    if max_rows:
        frame = frame.iloc[:max_rows].copy()
    return frame, features, categorical


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb", type=Path, default=DEFAULT_DUCKDB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-rows", type=int, default=0, help="Smoke subset only, not full-data evidence")
    parser.add_argument("--n-estimators", type=int, default=150)
    parser.add_argument("--windows", type=int, default=3, help="Expanding CV windows inside development data")
    parser.add_argument("--min-train-rows", type=int, default=10_000)
    parser.add_argument("--v-missingness-threshold", type=float, default=0.95)
    args = parser.parse_args(argv)
    if args.max_rows < 0 or args.n_estimators < 1 or args.windows < 0 or args.min_train_rows < 1:
        parser.error("Invalid integer settings")
    if not 0 <= args.v_missingness_threshold <= 1:
        parser.error("V missingness threshold must be in [0,1]")
    try:
        frame, features, categorical = read_local_features(args.duckdb, args.max_rows)
        result = benchmark(
            frame, features, categorical, args.n_estimators, args.windows,
            args.min_train_rows, args.v_missingness_threshold,
        )
    except (ValueError, FileNotFoundError, duckdb.Error) as exc:
        # Do not echo private filesystem paths.
        print(f"Experiment unavailable: {type(exc).__name__}")
        return 2
    result["subset_mode"] = bool(args.max_rows)
    result["source_duckdb_path_logged"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Experimental metrics written locally; {result['input_rows']} rows; source identity not published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
