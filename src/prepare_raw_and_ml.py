from __future__ import annotations

import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import matplotlib
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "kaggle_ieee_fraud"
ZIP_PATH = Path(
    os.environ.get(
        "IEEE_FRAUD_ZIP_PATH",
        str(RAW_DIR / "ieee-fraud-detection.zip"),
    )
)
DB_PATH = ROOT / "data" / "processed" / "ieee_fraud.duckdb"
TABLES_DIR = ROOT / "outputs" / "tables"
MODEL_VERSION = "lightgbm-v2-v339-missingness-filtered"
V_FEATURE_MISSINGNESS_THRESHOLD = float(os.environ.get("V_FEATURE_MISSINGNESS_THRESHOLD", "0.95"))
ROLLING_CV_WINDOWS = int(os.environ.get("ROLLING_CV_WINDOWS", "3"))
SHAP_SAMPLE_SIZE = int(os.environ.get("SHAP_SAMPLE_SIZE", "20000"))


REQUIRED_FILES = [
    "train_transaction.csv",
    "train_identity.csv",
    "test_transaction.csv",
    "test_identity.csv",
    "sample_submission.csv",
]


def ensure_dirs() -> None:
    for path in [RAW_DIR, DB_PATH.parent, TABLES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def ensure_raw_files() -> None:
    missing = [name for name in REQUIRED_FILES if not (RAW_DIR / name).exists()]
    if not missing:
        return
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Missing Kaggle zip: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(RAW_DIR)
    missing = [name for name in REQUIRED_FILES if not (RAW_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required files after extract: {missing}")


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def column_family(column_name: str) -> str:
    if column_name.startswith("V"):
        return "Vesta engineered V"
    if column_name.startswith("C"):
        return "Counting C"
    if column_name.startswith("D"):
        return "Timedelta D"
    if column_name.startswith("M"):
        return "Match M"
    if column_name.startswith("id_"):
        return "Identity id"
    if column_name.startswith("card"):
        return "Card"
    if column_name.startswith("addr"):
        return "Address"
    if column_name.startswith("dist"):
        return "Distance"
    if "emaildomain" in column_name:
        return "Email"
    return "Core transaction"


def table_columns(con: duckdb.DuckDBPyConnection, table_ref: str) -> list[str]:
    info = con.execute(f"pragma table_info('{table_ref}')").fetch_df()
    return info["name"].tolist()


def selected_v_features(con: duckdb.DuckDBPyConnection, txn_cols: set[str]) -> list[str]:
    """Select V1-V339 features while excluding structurally sparse columns."""

    candidates = [f"V{i}" for i in range(1, 340) if f"V{i}" in txn_cols]
    try:
        missingness = con.execute(
            """
            select column_name, missing_rate
            from raw.feature_missingness
            where table_name = 'train_transaction'
              and regexp_matches(column_name, '^V[0-9]+$')
            """
        ).fetch_df()
        missing_rate = dict(zip(missingness["column_name"], missingness["missing_rate"], strict=False))
    except duckdb.CatalogException:
        missing_rate = {}

    selected = [
        col
        for col in candidates
        if float(missing_rate.get(col, 0.0)) <= V_FEATURE_MISSINGNESS_THRESHOLD
    ]
    return selected or candidates


def build_raw_tables(con: duckdb.DuckDBPyConnection) -> dict:
    con.execute("create schema if not exists raw")
    table_map = {
        "train_transaction": RAW_DIR / "train_transaction.csv",
        "train_identity": RAW_DIR / "train_identity.csv",
        "test_transaction": RAW_DIR / "test_transaction.csv",
        "test_identity": RAW_DIR / "test_identity.csv",
        "sample_submission": RAW_DIR / "sample_submission.csv",
    }
    for table, path in table_map.items():
        con.execute(
            f"""
            create or replace table raw.{table} as
            select * from read_csv_auto(
                '{sql_path(path)}',
                header=true,
                sample_size=200000,
                nullstr=['', 'NA', 'null']
            )
            """
        )
        for col in table_columns(con, f"raw.{table}"):
            normalized = col.replace("-", "_")
            if normalized != col:
                con.execute(f"alter table raw.{table} rename column {quote(col)} to {quote(normalized)}")
    profile = {}
    for table in table_map:
        profile[table] = {
            "rows": int(con.execute(f"select count(*) from raw.{table}").fetchone()[0]),
            "columns": len(table_columns(con, f"raw.{table}")),
        }
    return profile


def build_missingness(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    frames = []
    for table in ["train_transaction", "train_identity", "test_transaction", "test_identity"]:
        cols = table_columns(con, f"raw.{table}")
        expressions = ["count(*) as row_count"]
        for col in cols:
            expressions.append(f"sum(case when {quote(col)} is null then 1 else 0 end) as {quote(col)}")
        row = con.execute(f"select {', '.join(expressions)} from raw.{table}").fetch_df().iloc[0]
        row_count = int(row["row_count"])
        for col in cols:
            missing_count = int(row[col])
            frames.append(
                {
                    "table_name": table,
                    "column_name": col,
                    "column_family": column_family(col),
                    "row_count": row_count,
                    "missing_count": missing_count,
                    "missing_rate": missing_count / row_count if row_count else 0,
                }
            )
    df = pd.DataFrame(frames)
    con.register("feature_missingness_df", df)
    con.execute("create or replace table raw.feature_missingness as select * from feature_missingness_df")
    return df


def available_feature_columns(con: duckdb.DuckDBPyConnection) -> tuple[list[str], list[str], list[str]]:
    txn_cols = set(table_columns(con, "raw.train_transaction"))
    id_cols = set(table_columns(con, "raw.train_identity"))
    v_features = selected_v_features(con, txn_cols)

    categorical = [
        "ProductCD",
        "card4",
        "card6",
        "P_emaildomain",
        "R_emaildomain",
        *[f"M{i}" for i in range(1, 10)],
    ]
    categorical += [
        "id_12",
        "id_15",
        "id_16",
        "id_28",
        "id_29",
        "id_31",
        "id_35",
        "id_36",
        "id_37",
        "id_38",
        "DeviceType",
        "DeviceInfo",
    ]

    numeric = [
        "TransactionDT",
        "TransactionAmt",
        "card1",
        "card2",
        "card3",
        "card5",
        "addr1",
        "addr2",
        "dist1",
        "dist2",
        *[f"C{i}" for i in range(1, 15)],
        *[f"D{i}" for i in range(1, 16)],
        *v_features,
        "id_01",
        "id_02",
        "id_03",
        "id_04",
        "id_05",
        "id_06",
        "id_09",
        "id_10",
        "id_11",
        "id_13",
        "id_14",
        "id_17",
        "id_18",
        "id_19",
        "id_20",
        "id_21",
        "id_22",
        "id_24",
        "id_25",
        "id_26",
        "id_32",
    ]

    selected = []
    for col in numeric + categorical:
        if col in txn_cols or col in id_cols:
            selected.append(col)
    categorical = [col for col in categorical if col in selected]
    numeric = [col for col in numeric if col in selected]
    return selected, numeric, categorical


def feature_query(split: str, features: list[str]) -> str:
    txn_table = "train_transaction" if split == "train" else "test_transaction"
    id_table = "train_identity" if split == "train" else "test_identity"
    txn_cols = {"TransactionID", "isFraud", "TransactionDT", "TransactionAmt"}

    select_parts = ['t."TransactionID" as "TransactionID"']
    if split == "train":
        select_parts.append('t."isFraud" as "isFraud"')
    for col in features:
        prefix = "t" if col in txn_cols or not col.startswith("id_") and col not in {"DeviceType", "DeviceInfo"} else "i"
        if col in {"id_12", "id_15", "id_16", "id_28", "id_29", "id_31", "id_35", "id_36", "id_37", "id_38", "DeviceType", "DeviceInfo"} or col.startswith("id_"):
            prefix = "i"
        select_parts.append(f"{prefix}.{quote(col)} as {quote(col)}")
    return f"""
        select {', '.join(select_parts)}
        from raw.{txn_table} as t
        left join raw.{id_table} as i
            on t."TransactionID" = i."TransactionID"
        order by t."TransactionDT"
    """


def encode_categoricals(train_df: pd.DataFrame, test_df: pd.DataFrame, categorical: list[str]) -> None:
    for col in categorical:
        train_values = train_df[col].astype("string").fillna("__missing__")
        categories = pd.Index(train_values.unique())
        mapping = pd.Series(np.arange(len(categories), dtype=np.int32), index=categories)
        train_df[col] = train_values.map(mapping).fillna(-1).astype("int32")
        test_df[col] = test_df[col].astype("string").fillna("__missing__").map(mapping).fillna(-1).astype("int32")


def lightgbm_model(n_estimators: int = 500) -> LGBMClassifier:
    return LGBMClassifier(
        objective="binary",
        n_estimators=n_estimators,
        learning_rate=0.035,
        num_leaves=64,
        subsample=0.85,
        colsample_bytree=0.85,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )


def rolling_time_cv_metrics(
    X: pd.DataFrame,
    y: pd.Series,
    transaction_dt: pd.Series,
    windows: int = ROLLING_CV_WINDOWS,
) -> pd.DataFrame:
    """Run expanding-window validation slices to surface concept drift risk."""

    order = transaction_dt.sort_values().index
    X_ordered = X.loc[order].reset_index(drop=True)
    y_ordered = y.loc[order].reset_index(drop=True)
    dt_ordered = transaction_dt.loc[order].reset_index(drop=True)

    row_count = len(y_ordered)
    min_train_rows = max(int(row_count * 0.4), 10_000)
    if row_count <= min_train_rows or windows < 1:
        return pd.DataFrame()

    window_size = max((row_count - min_train_rows) // windows, 1)
    records = []
    for window_number in range(1, windows + 1):
        valid_start = min_train_rows + (window_number - 1) * window_size
        valid_end = min_train_rows + window_number * window_size
        if window_number == windows:
            valid_end = row_count
        if valid_start >= row_count or valid_end <= valid_start:
            continue

        y_valid = y_ordered.iloc[valid_start:valid_end]
        if y_valid.nunique(dropna=True) < 2:
            continue

        model = lightgbm_model(n_estimators=300)
        model.fit(X_ordered.iloc[:valid_start], y_ordered.iloc[:valid_start])
        pred_valid = model.predict_proba(X_ordered.iloc[valid_start:valid_end])[:, 1]
        auc = float(roc_auc_score(y_valid, pred_valid))
        ap = float(average_precision_score(y_valid, pred_valid))
        records.append(
            {
                "window_number": window_number,
                "train_rows": int(valid_start),
                "validation_rows": int(valid_end - valid_start),
                "validation_start_dt": int(dt_ordered.iloc[valid_start]),
                "validation_end_dt": int(dt_ordered.iloc[valid_end - 1]),
                "fraud_rate": float(y_valid.mean()),
                "roc_auc": auc,
                "average_precision": ap,
                "concept_drift_flag": "Potential drift" if auc < 0.88 or ap < 0.45 else "Stable",
            }
        )

    return pd.DataFrame(records)


def train_and_score(con: duckdb.DuckDBPyConnection) -> dict:
    raw_tables = [
        row[0] for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='raw'"
        ).fetchall()
    ]
    if "feature_missingness" not in raw_tables:
        build_missingness(con)

    features, numeric, categorical = available_feature_columns(con)

    train_df = con.execute(feature_query("train", features)).fetch_df()
    test_df = con.execute(feature_query("test", features)).fetch_df()

    for col in numeric:
        if col not in train_df.columns:
            continue
        train_df[col] = pd.to_numeric(train_df[col], errors="coerce").astype("float32")
        test_df[col] = pd.to_numeric(test_df[col], errors="coerce").astype("float32")
    numeric = [c for c in numeric if c in train_df.columns]
    categorical = [c for c in categorical if c in train_df.columns]
    features = [c for c in features if c in train_df.columns]
    encode_categoricals(train_df, test_df, categorical)

    y = train_df["isFraud"].astype(int)
    cutoff = train_df["TransactionDT"].quantile(0.8)
    train_mask = train_df["TransactionDT"] <= cutoff
    X = train_df[features]
    X_train, X_valid = X.loc[train_mask], X.loc[~train_mask]
    y_train, y_valid = y.loc[train_mask], y.loc[~train_mask]

    rolling_cv = rolling_time_cv_metrics(X, y, train_df["TransactionDT"])
    if not rolling_cv.empty:
        rolling_cv.to_csv(TABLES_DIR / "rolling_cv_metrics.csv", index=False)
        con.register("rolling_cv_df", rolling_cv)
        con.execute("create or replace table raw.rolling_cv_metrics as select * from rolling_cv_df")

    model = lightgbm_model(n_estimators=500)
    model.fit(X_train, y_train)
    valid_pred = model.predict_proba(X_valid)[:, 1]
    auc = float(roc_auc_score(y_valid, valid_pred))
    ap = float(average_precision_score(y_valid, valid_pred))

    train_pred = model.predict_proba(X)[:, 1]
    test_pred = model.predict_proba(test_df[features])[:, 1]
    q80, q95, q99 = np.quantile(train_pred, [0.80, 0.95, 0.99])

    def risk_band(values: np.ndarray) -> np.ndarray:
        return np.select(
            [values >= q99, values >= q95, values >= q80],
            ["Critical", "High", "Elevated"],
            default="Low",
        )

    predictions = pd.concat(
        [
            pd.DataFrame(
                {
                    "transaction_id": train_df["TransactionID"].astype("int64"),
                    "split": "train",
                    "actual_is_fraud": y.astype("Int64"),
                    "predicted_fraud_probability": train_pred,
                    "risk_band": risk_band(train_pred),
                }
            ),
            pd.DataFrame(
                {
                    "transaction_id": test_df["TransactionID"].astype("int64"),
                    "split": "test",
                    "actual_is_fraud": pd.Series([pd.NA] * len(test_df), dtype="Int64"),
                    "predicted_fraud_probability": test_pred,
                    "risk_band": risk_band(test_pred),
                }
            ),
        ],
        ignore_index=True,
    )
    con.register("ml_predictions_df", predictions)
    con.execute("create or replace table raw.ml_predictions as select * from ml_predictions_df")

    feature_importance = pd.DataFrame(
        {
            "feature": features,
            "importance": model.feature_importances_,
            "feature_family": [column_family(col) for col in features],
        }
    ).sort_values("importance", ascending=False)
    con.register("feature_importance_df", feature_importance)
    con.execute("create or replace table raw.feature_importance as select * from feature_importance_df")
    feature_importance.to_csv(TABLES_DIR / "feature_importance.csv", index=False)

    # SHAP values add model explainability for the analyst-facing output layer.
    shap_frame = X_valid
    if len(shap_frame) > SHAP_SAMPLE_SIZE:
        shap_frame = shap_frame.sample(SHAP_SAMPLE_SIZE, random_state=42)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(shap_frame)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    shap_df = pd.DataFrame(
        {
            "feature": features,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            "feature_family": [column_family(col) for col in features],
        }
    ).sort_values("mean_abs_shap", ascending=False)
    con.register("shap_importance_df", shap_df)
    con.execute("create or replace table raw.shap_importance as select * from shap_importance_df")
    shap_df.to_csv(TABLES_DIR / "shap_importance.csv", index=False)
    shap.summary_plot(shap_values, shap_frame, feature_names=features, show=False)
    plt.savefig(TABLES_DIR / "shap_summary.png", bbox_inches="tight", dpi=150)
    plt.close()

    fpr, tpr, thresholds = roc_curve(y_valid, valid_pred)
    pd.DataFrame({"fpr": fpr, "tpr": tpr, "threshold": thresholds}).to_csv(
        TABLES_DIR / "validation_roc_curve.csv", index=False
    )
    validation_predictions = pd.DataFrame(
        {
            "transaction_id": train_df.loc[~train_mask, "TransactionID"].astype("int64").to_numpy(),
            "actual_is_fraud": y_valid.to_numpy(),
            "predicted_fraud_probability": valid_pred,
        }
    )
    validation_predictions.to_csv(TABLES_DIR / "validation_predictions.csv", index=False)
    con.register("validation_predictions_df", validation_predictions)
    con.execute("create or replace table raw.validation_predictions as select * from validation_predictions_df")

    threshold_values = [
        0.01,
        0.02,
        0.03,
        0.04,
        0.05,
        0.06,
        0.07,
        0.08,
        0.09,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.40,
        0.50,
    ]
    total_valid = len(validation_predictions)
    total_fraud_valid = int(validation_predictions["actual_is_fraud"].sum())
    threshold_records = []
    for threshold_value in threshold_values:
        selected_mask = validation_predictions["predicted_fraud_probability"] >= threshold_value
        reviewed = validation_predictions.loc[selected_mask]
        captured_fraud = int(reviewed["actual_is_fraud"].sum())
        false_positive_count = int(len(reviewed) - captured_fraud)
        false_negative_count = int(total_fraud_valid - captured_fraud)
        threshold_records.append(
            {
                "score_threshold": threshold_value,
                "evidence_scope": "validation_holdout",
                "review_count": int(len(reviewed)),
                "captured_fraud_count": captured_fraud,
                "false_positive_count": false_positive_count,
                "false_negative_count": false_negative_count,
                "workload_share": len(reviewed) / total_valid if total_valid else 0,
                "fraud_capture_rate": captured_fraud / total_fraud_valid if total_fraud_valid else 0,
                "precision_rate": captured_fraud / len(reviewed) if len(reviewed) else 0,
                "false_positive_rate": false_positive_count
                / max(total_valid - total_fraud_valid, 1),
                "operating_mode": (
                    "Broad monitoring"
                    if threshold_value <= 0.03
                    else "Balanced threshold policy"
                    if threshold_value <= 0.08
                    else "Focused risk policy"
                    if threshold_value <= 0.20
                    else "Narrow critical policy"
                ),
            }
        )
    validation_thresholds = pd.DataFrame(threshold_records)
    validation_thresholds.to_csv(TABLES_DIR / "validation_threshold_simulation.csv", index=False)
    con.register("validation_threshold_simulation_df", validation_thresholds)
    con.execute(
        "create or replace table raw.validation_threshold_simulation "
        "as select * from validation_threshold_simulation_df"
    )

    v_features_used = [col for col in features if col.startswith("V") and col[1:].isdigit()]
    rolling_records = rolling_cv.to_dict("records") if not rolling_cv.empty else []
    rolling_auc_values = [record["roc_auc"] for record in rolling_records]
    rolling_ap_values = [record["average_precision"] for record in rolling_records]
    model_registry = {
        "model_name": "LightGBMClassifier",
        "model_version": MODEL_VERSION,
        "training_date": datetime.now(UTC).isoformat(),
        "validation_strategy": "time-based holdout plus expanding rolling cross-validation",
        "data_scope": {
            "raw_train_transactions": int(len(train_df)),
            "fraud_rate": float(y.mean()),
            "transaction_dt_note": "TransactionDT is a relative timedelta, not a calendar timestamp.",
        },
        "feature_scope": {
            "feature_count": int(len(features)),
            "categorical_feature_count": int(len(categorical)),
            "v_feature_range": "V1-V339",
            "v_missingness_threshold": float(V_FEATURE_MISSINGNESS_THRESHOLD),
            "v_features_selected": int(len(v_features_used)),
            "feature_selection_note": "Anonymous Vesta V features are included when train missingness is at or below the configured ceiling.",
        },
        "holdout_metrics": {
            "roc_auc": float(auc),
            "average_precision": float(ap),
        },
        "rolling_cv_summary": {
            "window_count": int(len(rolling_records)),
            "roc_auc_mean": float(np.mean(rolling_auc_values)) if rolling_auc_values else None,
            "roc_auc_min": float(np.min(rolling_auc_values)) if rolling_auc_values else None,
            "average_precision_mean": float(np.mean(rolling_ap_values)) if rolling_ap_values else None,
            "average_precision_min": float(np.min(rolling_ap_values)) if rolling_ap_values else None,
        },
        "rolling_cv_windows": rolling_records,
        "risk_thresholds": {"elevated_p80": float(q80), "high_p95": float(q95), "critical_p99": float(q99)},
    }
    (TABLES_DIR / "model_registry.json").write_text(json.dumps(model_registry, indent=2), encoding="utf-8")
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "model_registry.json").write_text(json.dumps(model_registry, indent=2), encoding="utf-8")
    con.register(
        "model_registry_df",
        pd.DataFrame(
            [
                {
                    "model_version": MODEL_VERSION,
                    "training_date": model_registry["training_date"],
                    "feature_count": len(features),
                    "v_features_selected": len(v_features_used),
                    "holdout_roc_auc": auc,
                    "holdout_average_precision": ap,
                    "rolling_cv_auc_mean": model_registry["rolling_cv_summary"]["roc_auc_mean"],
                    "registry_json": json.dumps(model_registry),
                }
            ]
        ),
    )
    con.execute("create or replace table raw.model_registry as select * from model_registry_df")

    metrics = {
        "model": "LightGBMClassifier",
        "model_version": MODEL_VERSION,
        "validation_strategy": "time-based holdout: last 20% by TransactionDT",
        "validation_auc": auc,
        "validation_average_precision": ap,
        "features_used": len(features),
        "v_features_selected": len(v_features_used),
        "rolling_cv_windows": len(rolling_records),
        "rolling_cv_auc_mean": model_registry["rolling_cv_summary"]["roc_auc_mean"],
        "categorical_features": len(categorical),
        "v_features_included": len([f for f in features if f.startswith("V")]),
        "risk_thresholds": {"elevated_p80": float(q80), "high_p95": float(q95), "critical_p99": float(q99)},
        "rolling_cv": {
            "n_splits": len(rolling_records),
            "mean_auc": model_registry["rolling_cv_summary"]["roc_auc_mean"],
            "windows": rolling_records,
            "interpretation": (
                "Rolling windows reveal temporal stability. "
                "Stable AUC across folds = low concept drift risk; "
                "declining AUC = consider more frequent retraining."
            ),
        },
    }

    return metrics


def main() -> None:
    ensure_dirs()
    ensure_raw_files()
    con = duckdb.connect(str(DB_PATH))
    profile = build_raw_tables(con)
    missingness = build_missingness(con)
    ml_metrics = train_and_score(con)

    summary = {
        "source": "Official Kaggle IEEE-CIS Fraud Detection competition zip",
        "duckdb_path": str(DB_PATH),
        "tables": profile,
        "missingness_rows": int(len(missingness)),
        "ml": ml_metrics,
    }
    (TABLES_DIR / "raw_profile.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
