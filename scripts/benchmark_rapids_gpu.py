"""Time the IEEE-CIS feature pipeline and model on CPU (pandas + XGBoost) and GPU (RAPIDS cuDF + XGBoost CUDA).

The same code path runs on both engines, because cuDF follows the pandas API:

    # Linux or WSL2 with an NVIDIA GPU
    pip install --extra-index-url=https://pypi.nvidia.com "cudf-cu13" pandas pyarrow xgboost scikit-learn
    python scripts/benchmark_rapids_gpu.py --data <dir with train_transaction.csv, train_identity.csv> \
        --engine pandas --out results/cpu.json
    python scripts/benchmark_rapids_gpu.py --data <same dir> --engine cudf --out results/gpu.json

Each run times: CSV read, identity join, V-column missingness filter (the pipeline's 0.95 rule), categorical
encoding, a small set of group-by aggregates, and XGBoost training on the same time-ordered 80/20 split the
pipeline uses (TransactionDT). It then reports ROC-AUC / average precision on the later 20%.

This is a speed benchmark of one feature/model recipe on two engines. It does not replace the published
LightGBM model in src/prepare_raw_and_ml.py, and its AUC is not that model's AUC.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

V_MISSINGNESS_THRESHOLD = 0.95
CATEGORICAL = [
    "ProductCD", "card4", "card6", "P_emaildomain", "R_emaildomain", *[f"M{i}" for i in range(1, 10)],
    "id_12", "id_15", "id_16", "id_28", "id_29", "id_31", "id_35", "id_36", "id_37", "id_38",
    "DeviceType", "DeviceInfo",
]
NUMERIC_TXN = [
    "TransactionDT", "TransactionAmt", "card1", "card2", "card3", "card5", "addr1", "addr2", "dist1", "dist2",
    *[f"C{i}" for i in range(1, 15)], *[f"D{i}" for i in range(1, 16)],
]
NUMERIC_ID = [f"id_{i:02d}" for i in (1, 2, 3, 4, 5, 6, 9, 10, 11, 13, 14, 17, 18, 19, 20, 21, 22, 24, 25, 26, 32)]
V_CANDIDATES = [f"V{i}" for i in range(1, 340)]
# Group-by aggregates commonly used on this dataset; they exercise the engine's hash group-by and join.
AGGREGATES = [("card1", "TransactionAmt"), ("addr1", "TransactionAmt"), ("P_emaildomain", "TransactionAmt")]

XGB_PARAMS = {
    "n_estimators": 500, "max_depth": 8, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.5,
    "tree_method": "hist", "eval_metric": "auc", "random_state": 42,
}


class Timer:
    def __init__(self):
        self.steps: dict[str, float] = {}

    def __call__(self, name, fn, sync=None):
        t0 = time.perf_counter()
        out = fn()
        if sync:
            sync()
        self.steps[name] = round(time.perf_counter() - t0, 3)
        print(f"  {name}: {self.steps[name]}s", flush=True)
        return out


def engine_module(engine):
    if engine == "cudf":
        import cudf
        import cupy

        return cudf, cupy.cuda.runtime.deviceSynchronize
    import pandas

    return pandas, None


def read_inputs(xd, data_dir):
    txn_header = xd.read_csv(Path(data_dir) / "train_transaction.csv", nrows=0).columns
    id_header = xd.read_csv(Path(data_dir) / "train_identity.csv", nrows=0).columns
    txn_cols = ["TransactionID", "isFraud"] + [c for c in NUMERIC_TXN + CATEGORICAL + V_CANDIDATES if c in txn_header]
    id_cols = ["TransactionID"] + [c for c in NUMERIC_ID + CATEGORICAL if c in id_header]
    float_cols = {c: "float32" for c in NUMERIC_TXN + NUMERIC_ID + V_CANDIDATES}
    txn = xd.read_csv(Path(data_dir) / "train_transaction.csv", usecols=txn_cols,
                      dtype={c: t for c, t in float_cols.items() if c in txn_cols})
    ident = xd.read_csv(Path(data_dir) / "train_identity.csv", usecols=id_cols,
                        dtype={c: t for c, t in float_cols.items() if c in id_cols})
    return txn, ident


def drop_sparse_v(df):
    v = [c for c in V_CANDIDATES if c in df.columns]
    missing = df[v].isna().mean()
    if hasattr(missing, "to_pandas"):
        missing = missing.to_pandas()
    drop = [c for c, rate in missing.items() if rate > V_MISSINGNESS_THRESHOLD]
    return df.drop(columns=drop), len(v) - len(drop)


def encode_categoricals(df):
    for col in [c for c in CATEGORICAL if c in df.columns]:
        # pandas gives -1 for missing values; cuDF gives null, so fill to match.
        df[col] = df[col].astype("category").cat.codes.fillna(-1).astype("int32")
    return df


def add_aggregates(df):
    # groupby().transform() adds each aggregate as one column, without copying the whole frame through a merge.
    for key, value in AGGREGATES:
        grouped = df.groupby(key)[value]
        for stat in ("mean", "std", "count"):
            df[f"{value}_{stat}_by_{key}"] = grouped.transform(stat).astype("float32")
    return df


def run_once(xd, sync, data_dir, params):
    import xgboost
    from sklearn.metrics import average_precision_score, roc_auc_score

    timer = Timer()
    txn, ident = timer("read_csv", lambda: read_inputs(xd, data_dir), sync)
    # V columns live in the transaction table; dropping the sparse ones before the join keeps peak memory low.
    txn, n_v = timer("drop_sparse_v_columns", lambda: drop_sparse_v(txn), sync)
    df = timer("join_identity", lambda: txn.merge(ident, on="TransactionID", how="left"), sync)
    txn = ident = None  # release the inputs before the next steps
    df = timer("sort_by_time", lambda: df.sort_values("TransactionDT").reset_index(drop=True), sync)
    df = timer("encode_categoricals", lambda: encode_categoricals(df), sync)
    df = timer("groupby_aggregates", lambda: add_aggregates(df), sync)

    cutoff = float(df["TransactionDT"].quantile(0.8))
    features = [c for c in df.columns if c not in ("TransactionID", "isFraud")]
    train, valid = df[df["TransactionDT"] <= cutoff], df[df["TransactionDT"] > cutoff]
    model = xgboost.XGBClassifier(**params)
    timer("xgboost_fit", lambda: model.fit(train[features], train["isFraud"]), sync)
    proba = timer("xgboost_predict", lambda: model.predict_proba(valid[features])[:, 1], sync)

    y_valid = valid["isFraud"]
    if hasattr(y_valid, "to_numpy"):
        y_valid = y_valid.to_numpy()
    if hasattr(y_valid, "get"):
        y_valid = y_valid.get()
    if hasattr(proba, "get"):
        proba = proba.get()

    return {
        "rows": int(len(df)),
        "train_rows": int(len(train)),
        "valid_rows": int(len(valid)),
        "features": len(features),
        "v_columns_kept": n_v,
        "steps_s": timer.steps,
        "pipeline_total_s": round(sum(v for k, v in timer.steps.items() if not k.startswith("xgboost")), 3),
        "total_s": round(sum(timer.steps.values()), 3),
        "valid_roc_auc": round(float(roc_auc_score(y_valid, proba)), 4),
        "valid_average_precision": round(float(average_precision_score(y_valid, proba)), 4),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--engine", choices=["pandas", "cudf"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-estimators", type=int, default=XGB_PARAMS["n_estimators"])
    ap.add_argument("--repeats", type=int, default=2,
                    help="runs in one process; the first includes one-time GPU kernel compilation")
    ap.add_argument("--label", default="", help="free-text note stored in the report, e.g. the CPU core limit")
    a = ap.parse_args()

    import os

    import xgboost

    xd, sync = engine_module(a.engine)
    device = "cuda" if a.engine == "cudf" else "cpu"
    params = {**XGB_PARAMS, "n_estimators": a.n_estimators, "device": device}
    runs = []
    for i in range(a.repeats):
        print(f"engine={a.engine} model device={device} run {i + 1}/{a.repeats}", flush=True)
        runs.append(run_once(xd, sync, a.data, params))

    report = {
        "engine": a.engine,
        "model_device": device,
        "label": a.label,
        "cold_run": runs[0],
        "warm_run": runs[-1],
        "xgboost_params": params,
        "cpu_count_visible": os.cpu_count(),
        "platform": platform.platform(),
        "versions": {"xgboost": xgboost.__version__, xd.__name__: xd.__version__, "python": platform.python_version()},
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1))
    for name in ("cold_run", "warm_run"):
        r = report[name]
        print(name, json.dumps({k: r[k] for k in ("pipeline_total_s", "total_s", "valid_roc_auc")}), flush=True)


if __name__ == "__main__":
    main()
