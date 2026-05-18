from __future__ import annotations

import json
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "ieee_fraud.duckdb"
CHART_DIR = ROOT / "outputs" / "charts"
PBI_DIR = ROOT / "outputs" / "powerbi"
TABLES_DIR = ROOT / "outputs" / "tables"

COLORS = {
    "ink": "#17212B",
    "muted": "#64748B",
    "grid": "#D9E2EC",
    "teal": "#0F766E",
    "blue": "#2563EB",
    "amber": "#B7791F",
    "red": "#B42318",
    "green": "#2F855A",
    "violet": "#6D28D9",
    "paper": "#F8FAFC",
}


def ensure_dirs() -> None:
    for path in [CHART_DIR, PBI_DIR, TABLES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def savefig(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def read(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetch_df()


def export_powerbi_tables(con: duckdb.DuckDBPyConnection) -> None:
    exports = {
        "mart_fraud_summary.csv": "select * from mart.mart_fraud_summary",
        "mart_daily_stats.csv": "select * from mart.mart_daily_stats",
        "mart_amount_bands.csv": "select * from mart.mart_amount_bands",
        "mart_product_device_stats.csv": "select * from mart.mart_product_device_stats",
        "mart_email_domain_stats.csv": "select * from mart.mart_email_domain_stats",
        "mart_feature_missingness.csv": "select * from mart.mart_feature_missingness",
        "mart_model_predictions.csv": "select * from mart.mart_model_predictions",
        "mart_risk_band_stats.csv": "select * from mart.mart_risk_band_stats",
        "fact_train_transactions.csv": """
            select
                f.transaction_id,
                f.transaction_day,
                f.transaction_week,
                f.time_window,
                f.transaction_amount,
                f.amount_band,
                f.product_cd_clean as product_cd,
                f.card_network,
                f.card_type,
                f.device_type_clean as device_type,
                f.purchaser_email_group,
                f.has_identity,
                f.is_fraud,
                p.predicted_fraud_probability,
                p.risk_band
            from intermediate.int_features as f
            left join mart.mart_model_predictions as p
                on f.transaction_id = p.transaction_id
                and p.split = 'train'
        """,
    }
    for filename, sql in exports.items():
        path = PBI_DIR / filename
        out_path = str(path).replace('\\', '/')
        con.execute(f"copy ({sql}) to '{out_path}' (header, delimiter ',')")


def chart_class_imbalance(summary: pd.DataFrame) -> None:
    row = summary.iloc[0]
    values = [row["legitimate_transactions"], row["fraud_transactions"]]
    labels = ["Legitimate", "Fraud"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bars = ax.bar(labels, values, color=[COLORS["teal"], COLORS["red"]], width=0.52)
    ax.set_title("Fraud is a rare-event classification problem", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Transaction count")
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", length=0)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{int(value):,}", ha="center", va="bottom", fontsize=11)
    ax.text(0.02, 0.88, f"Observed fraud rate: {pct(row['fraud_rate'])}", transform=ax.transAxes, color=COLORS["red"], fontsize=12, weight="bold")
    savefig(CHART_DIR / "01_class_imbalance.png")


def chart_daily(daily: pd.DataFrame) -> None:
    daily = daily.sort_values("transaction_day")
    daily["fraud_rate_ma7"] = daily["fraud_rate"].rolling(7, min_periods=1).mean()
    fig, ax1 = plt.subplots(figsize=(10, 4.8))
    ax1.plot(daily["transaction_day"], daily["fraud_rate_ma7"] * 100, color=COLORS["red"], linewidth=2.4, label="Fraud rate, 7-day MA")
    ax1.set_ylabel("Fraud rate (%)", color=COLORS["red"])
    ax1.tick_params(axis="y", labelcolor=COLORS["red"])
    ax1.grid(axis="y", color=COLORS["grid"])
    ax2 = ax1.twinx()
    ax2.fill_between(daily["transaction_day"], daily["transaction_count"], color=COLORS["blue"], alpha=0.16, label="Volume")
    ax2.set_ylabel("Transaction volume", color=COLORS["blue"])
    ax2.tick_params(axis="y", labelcolor=COLORS["blue"])
    ax1.set_title("Fraud risk moves across the observation window", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax1.set_xlabel("Relative transaction day")
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.spines[["top", "left"]].set_visible(False)
    savefig(CHART_DIR / "02_daily_fraud_rate.png")


def chart_amount_bands(amount: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(amount["amount_band"], amount["fraud_rate"] * 100, color=COLORS["amber"], width=0.58)
    ax.set_title("High-value bands carry materially different fraud exposure", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Fraud rate (%)")
    ax.set_xlabel("")
    ax.grid(axis="y", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", rotation=25, length=0)
    for index, row in amount.iterrows():
        ax.text(index, row["fraud_rate"] * 100, f"{row['fraud_rate'] * 100:.1f}%", ha="center", va="bottom", fontsize=9)
    savefig(CHART_DIR / "03_amount_bands.png")


def chart_product_device(product_device: pd.DataFrame) -> None:
    df = product_device.sort_values(["fraud_rate", "transaction_count"], ascending=[False, False]).head(12).copy()
    df["segment"] = df["product_cd"].astype(str) + " / " + df["device_type"].astype(str)
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.barh(df["segment"][::-1], df["fraud_rate"][::-1] * 100, color=COLORS["violet"])
    ax.set_title("Risk concentrates by product and identity coverage", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Fraud rate (%)")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "04_product_device_risk.png")


def chart_feature_importance() -> None:
    fi = pd.read_csv(TABLES_DIR / "feature_importance.csv").head(18)
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    ax.barh(fi["feature"][::-1], fi["importance"][::-1], color=COLORS["teal"])
    ax.set_title("Model signal is driven by engineered V/C/D families and identity fields", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("LightGBM split importance")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "05_feature_importance.png")


def chart_roc(metrics: dict) -> None:
    roc = pd.read_csv(TABLES_DIR / "validation_roc_curve.csv")
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    ax.plot(roc["fpr"], roc["tpr"], color=COLORS["blue"], linewidth=2.6)
    ax.plot([0, 1], [0, 1], color=COLORS["muted"], linestyle="--", linewidth=1)
    ax.set_title("Time-based validation confirms usable ranking power", loc="left", fontsize=14, weight="bold", color=COLORS["ink"])
    ax.text(0.58, 0.16, f"AUC {metrics['ml']['validation_auc']:.3f}", transform=ax.transAxes, fontsize=18, weight="bold", color=COLORS["blue"])
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.grid(color=COLORS["grid"])
    ax.spines[["top", "right"]].set_visible(False)
    savefig(CHART_DIR / "06_validation_roc.png")


def chart_missingness(missingness: pd.DataFrame) -> None:
    df = (
        missingness[missingness["table_name"].eq("train_transaction")]
        .groupby("column_family", as_index=False)
        .agg(avg_missing_rate=("missing_rate", "mean"), columns=("column_name", "count"))
        .sort_values("avg_missing_rate", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.barh(df["column_family"][::-1], df["avg_missing_rate"][::-1] * 100, color=COLORS["green"])
    ax.set_title("Missingness is structural, not random noise", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Average missing rate by feature family (%)")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "07_missingness_by_family.png")


def chart_risk_band(risk: pd.DataFrame) -> None:
    df = risk[risk["split"].eq("train")].copy()
    order = ["Low", "Elevated", "High", "Critical"]
    df["risk_band"] = pd.Categorical(df["risk_band"], categories=order, ordered=True)
    df = df.sort_values("risk_band")
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(df["risk_band"].astype(str), df["observed_fraud_rate"] * 100, color=[COLORS["teal"], COLORS["amber"], COLORS["violet"], COLORS["red"]])
    ax.set_title("Risk bands convert model scores into BI-ready monitoring", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Observed fraud rate (%)")
    ax.grid(axis="y", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", length=0)
    savefig(CHART_DIR / "08_risk_bands.png")


def chart_architecture() -> None:
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    def box(x, y, w, h, title, subtitle, color):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.025,rounding_size=0.12", linewidth=1.2, edgecolor=color, facecolor=color + "22")
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=12, weight="bold", color=COLORS["ink"])
        ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", fontsize=9.5, color=COLORS["muted"])

    def arrow(x1, y1, x2, y2, dashed=False):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=14, linewidth=1.5, color=COLORS["muted"], linestyle="--" if dashed else "-"))

    headers = [("INGEST", 1.0), ("STORAGE", 3.6), ("TRANSFORM", 6.1), ("ML", 3.6), ("VISUALIZE", 9.2)]
    for text, x in headers:
        ax.text(x, 6.45, text, fontsize=10.5, weight="bold", color=COLORS["muted"], ha="center")
    ax.plot([0.5, 11.5], [6.25, 6.25], color=COLORS["grid"], linewidth=1)

    box(0.5, 5.0, 2.1, 0.75, "Kaggle CSV", "train/test transaction + identity", COLORS["teal"])
    box(3.1, 5.0, 2.1, 0.75, "BigQuery Free Tier", "raw landing tables", COLORS["blue"])
    box(5.8, 5.0, 2.1, 0.75, "dbt Core", "staging + intermediate + marts", COLORS["violet"])
    box(8.9, 5.0, 2.1, 0.75, "Power BI", "executive dashboard", COLORS["amber"])
    arrow(2.6, 5.38, 3.1, 5.38)
    arrow(5.2, 5.38, 5.8, 5.38)
    arrow(7.9, 5.38, 8.9, 5.38)

    box(3.1, 3.6, 2.1, 0.75, "DuckDB Local", "zero-cost reproducible warehouse", COLORS["green"])
    box(5.8, 3.6, 2.1, 0.75, "Mart Layer", "daily, segment, risk, model tables", COLORS["violet"])
    box(8.9, 3.6, 2.1, 0.75, "Looker Studio", "optional BigQuery view", COLORS["red"])
    arrow(1.55, 5.0, 4.15, 4.35, dashed=True)
    arrow(5.2, 3.98, 5.8, 3.98)
    arrow(7.9, 3.98, 8.9, 3.98)

    box(0.5, 2.0, 2.1, 0.75, "Python / ML", "LightGBM + sklearn validation", "#3F3F46")
    box(3.1, 2.0, 2.1, 0.75, "ML Predictions", "probability + risk bands", COLORS["blue"])
    arrow(2.6, 2.38, 3.1, 2.38)
    arrow(5.2, 2.38, 6.5, 3.6, dashed=True)

    box(0.6, 0.55, 2.35, 0.65, "staging", "typed cleaning", COLORS["teal"])
    box(3.55, 0.55, 2.35, 0.65, "intermediate", "joins + features", COLORS["blue"])
    box(6.5, 0.55, 2.35, 0.65, "mart", "fraud metrics", COLORS["violet"])
    box(9.45, 0.55, 1.6, 0.65, "test", "QA gates", COLORS["amber"])
    arrow(2.95, 0.88, 3.55, 0.88)
    arrow(5.9, 0.88, 6.5, 0.88)
    arrow(8.85, 0.88, 9.45, 0.88)
    ax.text(6, 1.55, "DBT LAYERS", fontsize=10.5, weight="bold", color=COLORS["muted"], ha="center")
    savefig(CHART_DIR / "09_architecture.png")


def write_docs(summary: pd.DataFrame, metrics: dict) -> None:
    row = summary.iloc[0]
    executive = f"""# IEEE-CIS Fraud Detection Executive Summary

## Core Metrics

- Total transactions: {int(row['total_transactions']):,}
- Fraud transactions: {int(row['fraud_transactions']):,}
- Fraud rate: {pct(row['fraud_rate'])}
- Identity coverage: {pct(row['identity_coverage_rate'])}
- Median transaction amount: ${row['median_transaction_amount']:,.2f}
- P95 transaction amount: ${row['p95_transaction_amount']:,.2f}
- Validation AUC: {metrics['ml']['validation_auc']:.3f}
- Validation average precision: {metrics['ml']['validation_average_precision']:.3f}

## Board-Level Takeaway

The dataset is a rare-event fraud problem with strong engineered feature signal, structural missingness, and meaningful risk concentration by product, identity coverage, transaction amount, and model-derived risk band. The recommended analytics operating model is raw landing in BigQuery free tier, dbt Core transformations, Python/LightGBM scoring, and Power BI consumption from curated marts.
"""
    (TABLES_DIR / "executive_summary.md").write_text(executive, encoding="utf-8")

    dashboard = """# Power BI Dashboard Specification

## Data Sources

Import all CSV files from `outputs/powerbi/`.

## Relationships

- `fact_train_transactions[transaction_id]` to `mart_model_predictions[transaction_id]`
- Use `mart_daily_stats`, `mart_amount_bands`, `mart_product_device_stats`, and `mart_risk_band_stats` as aggregated pages when performance matters.

## Measures

```DAX
Transactions = COUNTROWS(fact_train_transactions)
Fraud Transactions = SUM(fact_train_transactions[is_fraud])
Fraud Rate = DIVIDE([Fraud Transactions], [Transactions])
Average Amount = AVERAGE(fact_train_transactions[transaction_amount])
Predicted Risk = AVERAGE(fact_train_transactions[predicted_fraud_probability])
High Risk Transactions =
CALCULATE([Transactions], fact_train_transactions[risk_band] IN {"High", "Critical"})
```

## Pages

1. Executive Overview: KPI cards, fraud-rate trend, risk-band split.
2. Segment Risk: product/device matrix, email-domain risk, amount-band exposure.
3. Model Monitoring: AUC, feature importance, prediction risk bands, observed fraud by band.
4. Data Quality: missingness by family, identity coverage, dbt test status.
5. Architecture: ingest, BigQuery/DuckDB warehouse, dbt layers, ML scoring, BI consumption.
"""
    (PBI_DIR / "powerbi_dashboard_spec.md").write_text(dashboard, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    metrics = json.loads((TABLES_DIR / "raw_profile.json").read_text(encoding="utf-8"))
    con = duckdb.connect(str(DB_PATH), read_only=True)

    summary = read(con, "select * from mart.mart_fraud_summary")
    daily = read(con, "select * from mart.mart_daily_stats")
    amount = read(con, "select * from mart.mart_amount_bands")
    product_device = read(con, "select * from mart.mart_product_device_stats")
    missingness = read(con, "select * from mart.mart_feature_missingness")
    risk = read(con, "select * from mart.mart_risk_band_stats")

    export_powerbi_tables(con)
    chart_class_imbalance(summary)
    chart_daily(daily)
    chart_amount_bands(amount)
    chart_product_device(product_device)
    chart_feature_importance()
    chart_roc(metrics)
    chart_missingness(missingness)
    chart_risk_band(risk)
    chart_architecture()
    write_docs(summary, metrics)
    print(f"Power BI files: {PBI_DIR}")
    print(f"Charts: {CHART_DIR}")


if __name__ == "__main__":
    main()
