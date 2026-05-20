from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "kaggle_ieee_fraud"
ZIP_PATH = Path(r"C:\Users\cinar\Downloads\ieee-fraud-detection.zip")
DB_PATH = ROOT / "data" / "processed" / "ieee_fraud.duckdb"
TABLES_DIR = ROOT / "outputs" / "tables"


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
        *[f"V{i}" for i in range(1, 121)],
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

    select_parts = [f't."TransactionID" as "TransactionID"']
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


def train_and_score(con: duckdb.DuckDBPyConnection) -> dict:
    features, numeric, categorical = available_feature_columns(con)
    train_df = con.execute(feature_query("train", features)).fetch_df()
    test_df = con.execute(feature_query("test", features)).fetch_df()

    for col in numeric:
        train_df[col] = pd.to_numeric(train_df[col], errors="coerce").astype("float32")
        test_df[col] = pd.to_numeric(test_df[col], errors="coerce").astype("float32")
    encode_categoricals(train_df, test_df, categorical)

    y = train_df["isFraud"].astype(int)
    cutoff = train_df["TransactionDT"].quantile(0.8)
    train_mask = train_df["TransactionDT"] <= cutoff
    X = train_df[features]
    X_train, X_valid = X.loc[train_mask], X.loc[~train_mask]
    y_train, y_valid = y.loc[train_mask], y.loc[~train_mask]

    model = LGBMClassifier(
        objective="binary",
        n_estimators=500,
        learning_rate=0.035,
        num_leaves=64,
        subsample=0.85,
        colsample_bytree=0.85,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
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

    # --- SHAP: modelin neden bu karari verdigi ---
    import shap
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_valid)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    shap_df = pd.DataFrame({
        "feature": features,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0),
        "feature_family": [column_family(col) for col in features],
    }).sort_values("mean_abs_shap", ascending=False)
    con.register("shap_importance_df", shap_df)
    con.execute("create or replace table raw.shap_importance as select * from shap_importance_df")
    shap_df.to_csv(TABLES_DIR / "shap_importance.csv", index=False)
    shap.summary_plot(shap_values, X_valid, feature_names=features, show=False)
    plt.savefig(TABLES_DIR / "shap_summary.png", bbox_inches="tight", dpi=150)
    plt.close()
    print("SHAP tamamlandi.")
    # --- SHAP sonu ---

    fpr, tpr, thresholds = roc_curve(y_valid, valid_pred)
    pd.DataFrame({"fpr": fpr, "tpr": tpr, "threshold": thresholds}).to_csv(
        TABLES_DIR / "validation_roc_curve.csv", index=False
    )
    pd.DataFrame({"actual": y_valid.to_numpy(), "prediction": valid_pred}).to_csv(
        TABLES_DIR / "validation_predictions.csv", index=False
    )

    metrics = {
        "model": "LightGBMClassifier",
        "validation_strategy": "time-based holdout: last 20% by TransactionDT",
        "validation_auc": auc,
        "validation_average_precision": ap,
        "features_used": len(features),
        "categorical_features": len(categorical),
        "risk_thresholds": {"elevated_p80": float(q80), "high_p95": float(q95), "critical_p99": float(q99)},
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