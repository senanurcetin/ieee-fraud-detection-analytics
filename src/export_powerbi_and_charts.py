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


def chart_product_lift(con: duckdb.DuckDBPyConnection, baseline: float) -> None:
    df = read(
        con,
        """
        select
            product_cd_clean as product_cd,
            count(*) as transaction_count,
            avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by fraud_rate desc
        """,
    )
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    bars = ax.bar(df["product_cd"], df["fraud_rate"] * 100, color=[COLORS["red"], COLORS["amber"], COLORS["violet"], COLORS["blue"], COLORS["teal"]])
    ax.axhline(baseline * 100, color=COLORS["ink"], linestyle="--", linewidth=1.2)
    ax.text(0.02, baseline * 100 + 0.25, f"Baseline {baseline * 100:.2f}%", color=COLORS["ink"], fontsize=9)
    ax.set_title("Product C is the primary risk outlier", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Fraud rate (%)")
    ax.set_ylim(0, df["fraud_rate"].max() * 100 * 1.22)
    ax.grid(axis="y", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", length=0)
    for bar, (_, row) in zip(bars, df.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.25, f"{row['fraud_rate'] * 100:.1f}%\n{int(row['transaction_count'] / 1000)}k", ha="center", fontsize=9)
    savefig(CHART_DIR / "10_product_lift.png")


def chart_identity_lift(con: duckdb.DuckDBPyConnection, baseline: float) -> None:
    df = read(
        con,
        """
        select
            case when has_identity = 1 then 'Identity present' else 'No identity record' end as identity_status,
            count(*) as transaction_count,
            avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by fraud_rate
        """,
    )
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.bar(df["identity_status"], df["fraud_rate"] * 100, color=[COLORS["teal"], COLORS["red"]], width=0.5)
    ax.axhline(baseline * 100, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_title("Identity coverage is a risk signal, not just data completeness", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Fraud rate (%)")
    ax.set_ylim(0, df["fraud_rate"].max() * 100 * 1.28)
    ax.grid(axis="y", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    for idx, row in df.iterrows():
        ax.text(idx, row["fraud_rate"] * 100 + 0.18, f"{row['fraud_rate'] * 100:.2f}%\n{int(row['transaction_count']):,}", ha="center", fontsize=10)
    savefig(CHART_DIR / "11_identity_lift.png")


def chart_card_heatmap(con: duckdb.DuckDBPyConnection) -> None:
    df = read(
        con,
        """
        select
            card_network,
            card_type,
            count(*) as transaction_count,
            avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        where card_network != 'Unknown' and card_type != 'Unknown'
        group by 1, 2
        having count(*) >= 1000
        """,
    )
    matrix = df.pivot(index="card_network", columns="card_type", values="fraud_rate").fillna(0) * 100
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    im = ax.imshow(matrix.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)), matrix.columns)
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    for i in range(len(matrix.index)):
        for j in range(len(matrix.columns)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.1f}%", ha="center", va="center", fontsize=10, color=COLORS["ink"])
    ax.set_title("Credit card combinations show higher fraud exposure", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label="Fraud rate (%)")
    ax.spines[:].set_visible(False)
    savefig(CHART_DIR / "12_card_payment_heatmap.png")


def chart_email_risk(con: duckdb.DuckDBPyConnection, baseline: float) -> None:
    df = read(con, "select * from mart.mart_email_domain_stats order by fraud_rate desc")
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.barh(df["purchaser_email_group"][::-1], df["fraud_rate"][::-1] * 100, color=COLORS["blue"])
    ax.axvline(baseline * 100, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_title("Email domain groups split risk into practical BI segments", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Fraud rate (%)")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "13_email_domain_risk.png")


def chart_amount_distribution(con: duckdb.DuckDBPyConnection) -> None:
    df = read(
        con,
        """
        select
            case when is_fraud = 1 then 'Fraud' else 'Legitimate' end as label,
            transaction_amount
        from intermediate.int_features
        where transaction_amount between 0 and 1500
        """,
    )
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    legit = df[df["label"].eq("Legitimate")]["transaction_amount"]
    fraud = df[df["label"].eq("Fraud")]["transaction_amount"]
    ax.hist(legit, bins=80, alpha=0.45, density=True, color=COLORS["teal"], label="Legitimate")
    ax.hist(fraud, bins=80, alpha=0.55, density=True, color=COLORS["red"], label="Fraud")
    ax.set_title("Fraud amount distribution over-indexes at both small and high values", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Transaction amount, capped at $1,500")
    ax.set_ylabel("Density")
    ax.legend(frameon=False)
    ax.grid(axis="y", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    savefig(CHART_DIR / "14_amount_distribution.png")


def chart_hourly_pattern(con: duckdb.DuckDBPyConnection) -> None:
    df = read(
        con,
        """
        select
            cast(floor((transaction_dt % 86400) / 3600) as integer) as transaction_hour,
            count(*) as transaction_count,
            avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by 1
        """,
    )
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.plot(df["transaction_hour"], df["fraud_rate"] * 100, color=COLORS["red"], linewidth=2.5, marker="o")
    ax1.set_ylabel("Fraud rate (%)", color=COLORS["red"])
    ax1.tick_params(axis="y", labelcolor=COLORS["red"])
    ax1.set_xticks(range(0, 24, 2))
    ax1.grid(axis="y", color=COLORS["grid"])
    ax2 = ax1.twinx()
    ax2.bar(df["transaction_hour"], df["transaction_count"], color=COLORS["blue"], alpha=0.18, width=0.8)
    ax2.set_ylabel("Transaction count", color=COLORS["blue"])
    ax2.tick_params(axis="y", labelcolor=COLORS["blue"])
    ax1.set_title("Within-day risk pattern adds monitoring context", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax1.set_xlabel("Relative hour of day from TransactionDT")
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.spines[["top", "left"]].set_visible(False)
    savefig(CHART_DIR / "15_hourly_pattern.png")


def chart_risk_lift(risk: pd.DataFrame, baseline: float) -> None:
    df = risk[risk["split"].eq("train")].copy()
    order = ["Low", "Elevated", "High", "Critical"]
    df["risk_band"] = pd.Categorical(df["risk_band"], categories=order, ordered=True)
    df = df.sort_values("risk_band")
    df["lift"] = df["observed_fraud_rate"] / baseline
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.bar(df["risk_band"].astype(str), df["lift"], color=[COLORS["teal"], COLORS["amber"], COLORS["violet"], COLORS["red"]])
    ax.axhline(1, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_title("Model risk bands create review queues with measurable lift", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Fraud-rate lift vs baseline")
    ax.grid(axis="y", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    for idx, (_, row) in enumerate(df.iterrows()):
        ax.text(idx, row["lift"] + 0.8, f"{row['lift']:.1f}x", ha="center", fontsize=10, weight="bold")
    savefig(CHART_DIR / "16_risk_band_lift.png")


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

1. Executive Overview: baseline fraud rate, Product C lift, identity lift, and model risk-band lift.
2. Product Identity: product-level fraud concentration and identity-present versus no-identity behavior.
3. Payment Email: card network/type heatmap and purchaser email-domain risk groups.
4. Amount Time: amount-band fraud rate, amount distribution, daily fraud drift, and relative-hour pattern.
5. Model Risk: feature importance, time-based ROC, risk bands, and observed fraud by score band.
6. Data Quality: structural missingness, identity coverage, dbt test status, and architecture context.

## Narrative

Start the presentation with the business question: where does fraud concentrate? Use the dashboard to prove that fraud is not random across product, identity, payment, email, amount, and time. Show the model only after the segment analysis, as the operational layer that turns those patterns into review queues.
"""
    (PBI_DIR / "powerbi_dashboard_spec.md").write_text(dashboard, encoding="utf-8")

    con = duckdb.connect(str(DB_PATH), read_only=True)
    product = read(
        con,
        """
        select product_cd_clean as product_cd, count(*) as transactions, avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by fraud_rate desc
        """,
    )
    identity = read(
        con,
        """
        select has_identity, count(*) as transactions, avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by has_identity
        """,
    )
    story = f"""# Analysis Story

## Central Question

Where does fraud concentrate, and how should a BI team monitor it?

## Key Findings

1. Fraud is rare but concentrated: baseline fraud rate is {pct(row['fraud_rate'])}.
2. Product risk is uneven: Product C fraud rate is {product.iloc[0]['fraud_rate'] * 100:.2f}% versus Product W at {product[product['product_cd'].eq('W')].iloc[0]['fraud_rate'] * 100:.2f}%.
3. Identity presence is a risk signal: identity-present transactions show {identity[identity['has_identity'].eq(1)].iloc[0]['fraud_rate'] * 100:.2f}% fraud versus {identity[identity['has_identity'].eq(0)].iloc[0]['fraud_rate'] * 100:.2f}% without identity records.
4. Amount risk is non-linear: <$25 and $250+ bands show higher fraud rates than mid-size purchases.
5. Payment attributes matter: credit card combinations over-index versus debit card combinations.
6. The model should be used as a monitoring/ranking layer: Critical risk band captures very high fraud-rate lift versus baseline.

## Recommended Narrative

Start with class imbalance, then prove that fraud is not random. Move through product, identity, amount, payment, email, and time patterns. End with model risk bands as an operational monitoring layer, not as a black-box final decision engine.
"""
    (TABLES_DIR / "analysis_story.md").write_text(story, encoding="utf-8")


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
    baseline = float(summary.iloc[0]["fraud_rate"])
    chart_product_lift(con, baseline)
    chart_identity_lift(con, baseline)
    chart_card_heatmap(con)
    chart_email_risk(con, baseline)
    chart_amount_distribution(con)
    chart_hourly_pattern(con)
    chart_risk_lift(risk, baseline)
    chart_architecture()
    write_docs(summary, metrics)
    print(f"Power BI files: {PBI_DIR}")
    print(f"Charts: {CHART_DIR}")


if __name__ == "__main__":
    main()
