"""Full-source, versioned retrospective calibration of the historical model family.

No cloud writes or dashboard snapshot replacement. All learned preprocessing is
fit on each core window; three earlier validation windows select the calibrator
before the final 20% is evaluated. This does not supply prospective bank evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import lightgbm
import numpy as np
import pandas as pd
import sklearn
from lightgbm import LGBMClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

MODEL_VERSION = "lightgbm-v3-temporal-calibrated-20261021"
PARAMETERS = dict(objective="binary", n_estimators=500, learning_rate=0.035,
                  num_leaves=64, subsample=0.85, colsample_bytree=0.85,
                  class_weight="balanced", random_state=42, n_jobs=2, verbose=-1)
CATEGORICAL = ["ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain",
               *[f"M{i}" for i in range(1, 10)], "id_12", "id_15", "id_16",
               "id_28", "id_29", "id_31", "id_35", "id_36", "id_37", "id_38",
               "DeviceType", "DeviceInfo"]
NUMERIC = ["TransactionDT", "TransactionAmt", "card1", "card2", "card3", "card5",
           "addr1", "addr2", "dist1", "dist2", *[f"C{i}" for i in range(1, 15)],
           *[f"D{i}" for i in range(1, 16)], *[f"V{i}" for i in range(1, 340)],
           *[f"id_{i:02d}" for i in [1, 2, 3, 4, 5, 6, 9, 10, 11, 13, 14,
                                     17, 18, 19, 20, 21, 22, 24, 25, 26, 32]]]


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_cut(times: np.ndarray, fraction: float) -> int:
    """Cut already ordered times before a whole timestamp group."""
    if not 0 < fraction < 1 or len(times) < 4 or not np.isfinite(times).all():
        raise ValueError("Invalid chronological cut")
    if np.any(np.diff(times) < 0):
        raise ValueError("Times must already be ordered")
    desired = max(1, min(int(len(times) * fraction), len(times) - 1))
    cut = int(np.searchsorted(times, times[desired], side="left"))
    if cut <= 0 or cut >= len(times) or times[cut - 1] >= times[cut]:
        raise ValueError("Cannot produce disjoint time windows")
    return cut


def window(frame: pd.DataFrame) -> dict[str, Any]:
    return {"rows": len(frame), "min_transaction_dt": float(frame.TransactionDT.min()),
            "max_transaction_dt": float(frame.TransactionDT.max()),
            "fraud_count": int(frame.isFraud.sum())}


def encode_core(core: pd.DataFrame, others: list[pd.DataFrame], features: list[str]):
    """Training-only V missingness and category vocabularies; ordinal legacy mode."""
    selected = [c for c in features if not (c.startswith("V") and c[1:].isdigit())
                or core[c].isna().mean() <= 0.95]
    if not selected:
        raise ValueError("No predictors survived")
    encoded = [pd.DataFrame(index=frame.index) for frame in [core, *others]]
    for col in selected:
        if col in CATEGORICAL:
            tokens = sorted(core[col].astype("string").dropna().unique().tolist())
            mapping = {value: i for i, value in enumerate(tokens)}
            for frame, output in zip([core, *others], encoded, strict=True):
                output[col] = frame[col].astype("string").map(mapping).fillna(-1).astype("int32")
        else:
            for frame, output in zip([core, *others], encoded, strict=True):
                output[col] = pd.to_numeric(frame[col], errors="coerce").astype("float32")
    return encoded, selected


def metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    y, p = np.asarray(labels, dtype="int8"), np.asarray(scores, dtype="float64")
    if y.ndim != 1 or p.shape != y.shape or not len(y) or not np.isin(y, [0, 1]).all():
        raise ValueError("Invalid labels/scores")
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("Scores must be finite probabilities")
    reliability, ece = [], 0.0
    for bucket in range(10):
        selected = (p >= bucket / 10) & (p < (bucket + 1) / 10 if bucket < 9 else p <= 1)
        n = int(selected.sum())
        if n:
            mean, observed = float(p[selected].mean()), float(y[selected].mean())
            ece += n / len(y) * abs(mean - observed)
            reliability.append({"bin": bucket, "count": n, "mean_score": mean,
                                "observed_rate": observed})
    order = np.argsort(-p, kind="stable")
    queues = {}
    for fraction in [0.01, 0.05, 0.1]:
        k = max(1, int(np.ceil(len(y) * fraction)))
        captured = int(y[order[:k]].sum())
        precision = captured / k
        z, denom = 1.96, 1 + 1.96 ** 2 / k
        center = (precision + z * z / (2 * k)) / denom
        half = z * np.sqrt(precision * (1 - precision) / k + z * z / (4 * k * k)) / denom
        queues[f"top_{round(100 * fraction)}pct"] = {
            "review_rows": k, "fraud_cases_captured": captured, "precision": precision,
            "recall": captured / int(y.sum()) if y.sum() else None,
            "precision_wilson_95pct": [float(center - half), float(center + half)]}
    both = len(np.unique(y)) == 2
    return {"rows": len(y), "fraud_count": int(y.sum()), "fraud_rate": float(y.mean()),
            "mean_score": float(p.mean()), "roc_auc": float(roc_auc_score(y, p)) if both else None,
            "average_precision": float(average_precision_score(y, p)) if both else None,
            "brier_score": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, p, labels=[0, 1])),
            "expected_calibration_error": float(ece), "reliability_bins": reliability,
            "top_k_review_queue": queues}


def fit_window(core: pd.DataFrame, calibration: pd.DataFrame, validation: pd.DataFrame,
               features: list[str]) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    for frame in [core, calibration, validation]:
        if frame.isFraud.nunique() != 2:
            raise ValueError("Each window needs both classes")
    if not core.TransactionDT.max() < calibration.TransactionDT.min():
        raise ValueError("Core/calibration overlap")
    if not calibration.TransactionDT.max() < validation.TransactionDT.min():
        raise ValueError("Calibration/validation overlap")
    matrices, selected = encode_core(core, [calibration, validation], features)
    model = LGBMClassifier(**PARAMETERS)
    model.fit(matrices[0], core.isFraud.astype(int))
    cal_scores = model.predict_proba(matrices[1])[:, 1]
    raw = model.predict_proba(matrices[2])[:, 1]
    ycal = calibration.isFraud.to_numpy(dtype="int8")
    # Sigmoid of raw-score log odds, fitted solely on the calibration window.
    cal_logit = np.log(np.clip(cal_scores, 1e-7, 1 - 1e-7) / np.clip(1 - cal_scores, 1e-7, 1))
    raw_logit = np.log(np.clip(raw, 1e-7, 1 - 1e-7) / np.clip(1 - raw, 1e-7, 1))
    platt = LogisticRegression(max_iter=1000, random_state=42).fit(cal_logit[:, None], ycal)
    isotonic = IsotonicRegression(out_of_bounds="clip").fit(cal_scores, ycal)
    scores = {"raw": raw, "platt": platt.predict_proba(raw_logit[:, None])[:, 1],
              "isotonic": isotonic.predict(raw), "constant": np.full(len(raw), float(ycal.mean()))}
    report = {"windows": {"core": window(core), "calibration": window(calibration), "validation": window(validation)},
              "feature_count": len(selected), "features_sha256": hashlib.sha256("\n".join(selected).encode()).hexdigest(),
              "feature_names": selected, "metrics": {name: metrics(validation.isFraud.to_numpy(), p) for name, p in scores.items()}}
    return report, scores


def select_method(folds: list[dict[str, Any]]) -> str:
    if len(folds) < 3:
        raise ValueError("Three completed development windows required")
    return min(["platt", "isotonic"], key=lambda name: (
        np.mean([fold["metrics"][name]["brier_score"] for fold in folds]), name))


def day_block_uncertainty(frame: pd.DataFrame, scores: np.ndarray, baseline: np.ndarray) -> dict[str, Any]:
    """Paired day-cluster bootstrap of mean Brier difference, conditional on fit."""
    y = frame.isFraud.to_numpy(dtype="int8")
    grouped = pd.DataFrame({"day": np.floor(frame.TransactionDT.to_numpy() / 86400),
                            "delta": (scores - y) ** 2 - (baseline - y) ** 2}).groupby("day").delta.agg(["sum", "count"])
    if len(grouped) < 2:
        raise ValueError("At least two time blocks required")
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(grouped), size=(1000, len(grouped)))
    diffs = grouped["sum"].to_numpy()[indices].sum(axis=1) / grouped["count"].to_numpy()[indices].sum(axis=1)
    low, high = np.quantile(diffs, [.025, .975])
    return {"method": "paired relative-day cluster percentile bootstrap, conditional on fixed fitted model",
            "blocks": len(grouped), "resamples": 1000, "seed": 42,
            "selected_minus_constant_brier": float(np.mean((scores - y) ** 2 - (baseline - y) ** 2)),
            "percentile_95pct": [float(low), float(high)],
            "limitation": "Does not capture model-fit or masked-customer cluster uncertainty; time blocks may remain dependent."}


def run_study(frame: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    if len(frame) != 590540 or frame.TransactionID.duplicated().any():
        raise ValueError("Require complete unique 590540-row training source")
    frame = frame.sort_values(["TransactionDT", "TransactionID"], kind="stable").reset_index(drop=True)
    if not frame.isFraud.isin([0, 1]).all() or not np.isfinite(frame.TransactionDT).all():
        raise ValueError("Invalid labels/times")
    if {"TransactionID", "isFraud"}.intersection(features):
        raise ValueError("Identifiers and target cannot be predictors")
    end_dev = strict_cut(frame.TransactionDT.to_numpy(), .8)
    development, final = frame.iloc[:end_dev], frame.iloc[end_dev:]
    times = development.TransactionDT.to_numpy()
    edges = [strict_cut(times, fraction) for fraction in [.5, 2 / 3, 5 / 6]] + [len(development)]
    folds = []
    for number, (a, b) in enumerate(zip(edges[:-1], edges[1:], strict=True), 1):
        prefix = development.iloc[:a]
        split = strict_cut(prefix.TransactionDT.to_numpy(), .75)
        print(f"Development fold {number}: {split} core, {a-split} calibration, {b-a} validation", flush=True)
        report, _ = fit_window(prefix.iloc[:split], prefix.iloc[split:], development.iloc[a:b], features)
        report["fold"] = number
        folds.append(report)
    selected = select_method(folds)
    print("Calibration method frozen before final evaluation:", selected, flush=True)
    split = strict_cut(development.TransactionDT.to_numpy(), .75)
    final_report, scores = fit_window(development.iloc[:split], development.iloc[split:], final, features)
    final_report["selected_method"] = selected
    m = final_report["metrics"]
    checks = {"brier_better_than_raw": m[selected]["brier_score"] < m["raw"]["brier_score"],
              "brier_better_than_constant": m[selected]["brier_score"] < m["constant"]["brier_score"],
              "log_loss_better_than_constant": m[selected]["log_loss"] < m["constant"]["log_loss"],
              "roc_auc_loss_at_most_0_01": m[selected]["roc_auc"] >= m["raw"]["roc_auc"] - .01}
    final_report["acceptance"] = {"accepted_for_retrospective_probability": all(checks.values()),
                                    "criteria": checks, "operational_approval": False}
    final_report["uncertainty"] = day_block_uncertainty(final, scores[selected], scores["constant"])
    final_report["time_windows"] = []
    # Fixed consecutive relative-time quartiles; descriptive post-fit diagnostics only.
    time_edges = np.linspace(final.TransactionDT.min(), final.TransactionDT.max() + 1, 5)
    for i in range(4):
        mask = (final.TransactionDT >= time_edges[i]) & (final.TransactionDT < time_edges[i + 1])
        if mask.any():
            final_report["time_windows"].append({"relative_time_quartile": i + 1,
                "window": window(final.loc[mask]),
                "metrics": {name: metrics(final.loc[mask, "isFraud"].to_numpy(), p[mask.to_numpy()]) for name, p in scores.items()}})
    return {"schema_version": 1, "study": "Full-source retrospective calibration and rolling temporal robustness",
            "model_version": MODEL_VERSION,
            "base_model_contract": {"name": "Historical LightGBM500 family, newly fitted version; not historical v2 weights",
                                    "hyperparameters": PARAMETERS,
                                    "feature_policy": "Same numeric/categorical candidate families incl V1-V339; V missingness <=0.95 and ordinal vocabularies learned on each core only"},
            "source": {"rows": len(frame), "subset_mode": False,
                       "ordered_rows_sha256": hashlib.sha256(pd.util.hash_pandas_object(frame[["TransactionID", "TransactionDT", "isFraud"]], index=False).values.tobytes()).hexdigest()},
            "development": {"folds": folds, "selected_method": selected,
                            "selection_rule": "Lowest unweighted mean Brier across three pre-final validation windows; alphabetic tie-break"},
            "final": final_report,
            "score_contract": {"risk_score": "Uncalibrated rank score from the new versioned LightGBM500 fit",
                               "calibrated_fraud_probability": f"{selected} transform fitted on the disjoint middle window of this model version only",
                               "scope": "retrospective IEEE-CIS historical research; aggregate report only",
                               "historical_v2_mapping": False, "not_for_live_decisions": True},
            "limitations": ["IEEE-CIS is already explored historical data; final is isolated within this execution, not a pristine prospective/external cohort.",
                            "Masked features and TransactionDT are proxies/relative time, not real identity or calendar dates.",
                            "New fold-fit preprocessing and 60/20/20 fit contract prevent attaching this calibration to historical v2 weights.",
                            "Three rolling windows and relative-day intervals do not prove robustness to all future shifts.",
                            "No customer blocking, prevented-loss or production deployment effectiveness claim."],
            "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                         "lightgbm": lightgbm.__version__, "sklearn": sklearn.__version__}}


def load_source(transaction: Path, identity: Path) -> tuple[pd.DataFrame, list[str]]:
    frames = []
    wanted = {"TransactionID", "TransactionDT", "isFraud", *NUMERIC, *CATEGORICAL}
    for path in [transaction, identity]:
        header = pd.read_csv(path, nrows=0).columns.tolist()
        columns = [name for name in header if name in wanted]
        types = {name: ("string" if name in CATEGORICAL else "float32") for name in columns}
        types.update({name: dtype for name, dtype in {"TransactionID": "int64", "TransactionDT": "float64", "isFraud": "int8"}.items() if name in columns})
        frame = pd.read_csv(path, usecols=columns, dtype=types)
        if frame.TransactionID.isna().any() or frame.TransactionID.duplicated().any():
            raise ValueError("Invalid join keys")
        frames.append(frame)
    if not frames[1].TransactionID.isin(frames[0].TransactionID).all():
        raise ValueError("Orphan identity keys")
    merged = frames[0].merge(frames[1], on="TransactionID", how="left", validate="one_to_one")
    return merged, [name for name in [*NUMERIC, *CATEGORICAL] if name in merged]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transaction", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("webapp/research/published-model-calibration.json"))
    args = parser.parse_args()
    frame, features = load_source(args.transaction, args.identity)
    result = run_study(frame, features)
    result["source"].update(transaction_sha256=file_digest(args.transaction), identity_sha256=file_digest(args.identity))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Study completed:", result["model_version"], result["final"]["acceptance"], flush=True)


if __name__ == "__main__":
    main()
