"""Reproduce IEEE-CIS random-vs-time holdout ranking, without model leakage.

This is a NEW comparison, not a reconstruction of the lost Kaggle notebook.
Requires the licensed Kaggle train_transaction.csv, not published in this repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import lightgbm
import numpy as np
import pandas as pd
import sklearn
from lightgbm import LGBMClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

SEED = 42
FEATURES = (
    ["TransactionAmt", "card1", "card2", "card3", "card5", "addr1", "addr2", "dist1", "dist2"]
    + [f"C{i}" for i in range(1, 15)]
    + [f"D{i}" for i in range(1, 16)]
    + [f"V{i}" for i in range(1, 21)]
)
CARD_PROXY = ["card1", "card2", "card3", "card5", "addr1"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_indices(frame: pd.DataFrame, seed: int = SEED) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    if frame["isFraud"].nunique() != 2 or frame["TransactionDT"].isna().any():
        raise ValueError("Both fraud classes and nonnull TransactionDT are required")
    indices = np.arange(len(frame))
    random_train, random_test = train_test_split(
        indices, test_size=0.20, random_state=seed, stratify=frame["isFraud"].to_numpy()
    )
    # Don't split records sharing the cutoff timestamp across time windows.
    times = frame["TransactionDT"].to_numpy()
    sorted_times = np.sort(times)
    threshold = sorted_times[int(0.8 * len(frame))]
    time_train, time_test = indices[times < threshold], indices[times >= threshold]
    if not len(time_train) or not len(time_test):
        raise ValueError("Chronological holdout cannot separate timestamps")
    assert times[time_train].max() < times[time_test].min()
    return {"random": (random_train, random_test), "chronological": (time_train, time_test)}


def card_proxy(frame: pd.DataFrame) -> pd.Series:
    # Masked attributes are not verified customer IDs. This is only a card-family proxy.
    present = [x for x in CARD_PROXY if x in frame.columns]
    if not present:
        raise ValueError("Card-family proxy columns are missing")
    return frame[present].astype("string").fillna("<NA>").agg("|".join, axis=1)


def ranking_metrics(y: np.ndarray, scores: np.ndarray) -> dict:
    if len(y) == 0:
        return {"n": 0, "fraud_rate": None, "roc_auc": None, "average_precision": None}
    valid = len(np.unique(y)) == 2
    return {
        "n": int(len(y)),
        "fraud_rate": round(float(np.mean(y)), 6),
        "roc_auc": round(float(roc_auc_score(y, scores)), 6) if valid else None,
        "average_precision": round(float(average_precision_score(y, scores)), 6) if valid else None,
    }


def compare(frame: pd.DataFrame, seed: int = SEED) -> dict:
    feature_names = [x for x in FEATURES if x in frame.columns]
    if not feature_names:
        raise ValueError("No allowed numeric predictors were found")
    X = frame[feature_names].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    y = frame["isFraud"].astype(int).to_numpy()
    group = card_proxy(frame).to_numpy()
    splits = split_indices(frame, seed)
    result = {}
    for name, (fit, holdout) in splits.items():
        model = LGBMClassifier(
            n_estimators=150, learning_rate=0.05, num_leaves=31,
            random_state=seed, n_jobs=2, verbosity=-1,
        )
        model.fit(X.iloc[fit], y[fit])
        scores = model.predict_proba(X.iloc[holdout])[:, 1]
        seen = np.isin(group[holdout], np.unique(group[fit]))
        result[name] = {
            "train_rows": int(len(fit)),
            "holdout_rows": int(len(holdout)),
            "holdout": ranking_metrics(y[holdout], scores),
            "seen_card_proxy_fraction": round(float(np.mean(seen)), 6),
            "seen_proxy_subset": ranking_metrics(y[holdout][seen], scores[seen]),
            "unseen_proxy_subset": ranking_metrics(y[holdout][~seen], scores[~seen]),
            "train_max_transaction_dt": float(frame["TransactionDT"].iloc[fit].max()),
            "holdout_min_transaction_dt": float(frame["TransactionDT"].iloc[holdout].min()),
        }
    return {
        "study": "IEEE-CIS random and chronological holdout, new reproduction",
        "seed": seed,
        "predictors": feature_names,
        "rows": int(len(frame)),
        "splits": result,
        "interpretation_limit": (
            "A random-vs-time score difference is not by itself a causal estimate of leakage; "
            "temporal distribution shift and card-family correlation can also affect it. "
            "Card attributes are masked proxies, not validated customer IDs."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="Original Kaggle train_transaction.csv")
    parser.add_argument("--output", type=Path, default=Path("outputs/research/ieee_cis_split_comparison.json"))
    parser.add_argument("--max-rows", type=int, default=0, help="Optional smoke subset; never call this full-data")
    args = parser.parse_args(argv)
    if args.max_rows < 0:
        parser.error("--max-rows must be >= 0")
    needed = {"isFraud", "TransactionDT", *FEATURES, *CARD_PROXY}
    df = pd.read_csv(args.csv, usecols=lambda c: c in needed, nrows=args.max_rows or None)
    if not {"isFraud", "TransactionDT"}.issubset(df.columns):
        raise ValueError("CSV missing required isFraud / TransactionDT columns")
    result = compare(df)
    result["input_sha256"] = file_sha256(args.csv)
    result["input_path_logged"] = False
    result["subset_mode"] = bool(args.max_rows)
    result["versions"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "pandas": pd.__version__, "lightgbm": lightgbm.__version__,
        "sklearn": sklearn.__version__,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
