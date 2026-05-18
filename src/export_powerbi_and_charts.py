from __future__ import annotations

import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
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
    labels = ["Normal", "Sahtecilik"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bars = ax.bar(labels, values, color=[COLORS["teal"], COLORS["red"]], width=0.52)
    ax.set_title("Sahtecilik nadir görülür, ancak belirgin şekilde ayrışır", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("İşlem sayısı")
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", length=0)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{int(value):,}", ha="center", va="bottom", fontsize=11)
    ax.text(0.02, 0.88, f"Gözlenen sahtecilik oranı: {pct(row['fraud_rate'])}", transform=ax.transAxes, color=COLORS["red"], fontsize=12, weight="bold")
    savefig(CHART_DIR / "01_class_imbalance.png")


def chart_daily(daily: pd.DataFrame) -> None:
    daily = daily.sort_values("transaction_day")
    daily["fraud_rate_ma7"] = daily["fraud_rate"].rolling(7, min_periods=1).mean()
    fig, ax1 = plt.subplots(figsize=(10, 4.8))
    ax1.plot(daily["transaction_day"], daily["fraud_rate_ma7"] * 100, color=COLORS["red"], linewidth=2.4, label="Sahtecilik oranı, 7 günlük HO")
    ax1.set_ylabel("Sahtecilik oranı (%)", color=COLORS["red"])
    ax1.tick_params(axis="y", labelcolor=COLORS["red"])
    ax1.grid(axis="y", color=COLORS["grid"])
    ax2 = ax1.twinx()
    ax2.fill_between(daily["transaction_day"], daily["transaction_count"], color=COLORS["blue"], alpha=0.16, label="Hacim")
    ax2.set_ylabel("İşlem hacmi", color=COLORS["blue"])
    ax2.tick_params(axis="y", labelcolor=COLORS["blue"])
    ax1.set_title("Sahtecilik riski gözlem penceresi boyunca değişiyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax1.set_xlabel("Göreli işlem günü")
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.spines[["top", "left"]].set_visible(False)
    savefig(CHART_DIR / "02_daily_fraud_rate.png")


def chart_amount_bands(amount: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(amount["amount_band"], amount["fraud_rate"] * 100, color=COLORS["amber"], width=0.58)
    ax.set_title("Tutar bantları sahtecilik riskini farklılaştırıyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Sahtecilik oranı (%)")
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
    ax.set_title("Risk ürün ve identity kapsamına göre yoğunlaşıyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Sahtecilik oranı (%)")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "04_product_device_risk.png")


def chart_feature_importance() -> None:
    fi = pd.read_csv(TABLES_DIR / "feature_importance.csv").head(18)
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    ax.barh(fi["feature"][::-1], fi["importance"][::-1], color=COLORS["teal"])
    ax.set_title("Model sinyali V/C/D aileleri ve identity alanlarından güç alıyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("LightGBM bölünme önemi")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "05_feature_importance.png")


def chart_roc(metrics: dict) -> None:
    roc = pd.read_csv(TABLES_DIR / "validation_roc_curve.csv")
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    ax.plot(roc["fpr"], roc["tpr"], color=COLORS["blue"], linewidth=2.6)
    ax.plot([0, 1], [0, 1], color=COLORS["muted"], linestyle="--", linewidth=1)
    ax.set_title("Zamana dayalı doğrulama sıralama gücünü doğruluyor", loc="left", fontsize=14, weight="bold", color=COLORS["ink"])
    ax.text(0.58, 0.16, f"AUC {metrics['ml']['validation_auc']:.3f}", transform=ax.transAxes, fontsize=18, weight="bold", color=COLORS["blue"])
    ax.set_xlabel("Yanlış pozitif oranı")
    ax.set_ylabel("Doğru pozitif oranı")
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
    ax.set_title("Eksiklik yapısal; rastgele gürültü değil", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Feature ailesi bazında ortalama eksiklik oranı (%)")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "07_missingness_by_family.png")


def chart_risk_band(risk: pd.DataFrame) -> None:
    df = risk[risk["split"].eq("train")].copy()
    order = ["Low", "Elevated", "High", "Critical"]
    df["risk_band"] = pd.Categorical(df["risk_band"], categories=order, ordered=True)
    df = df.sort_values("risk_band")
    label_map = {"Low": "Düşük", "Elevated": "Yükselen", "High": "Yüksek", "Critical": "Kritik"}
    df["risk_band_tr"] = df["risk_band"].astype(str).map(label_map)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(df["risk_band_tr"], df["observed_fraud_rate"] * 100, color=[COLORS["teal"], COLORS["amber"], COLORS["violet"], COLORS["red"]])
    ax.set_title("Risk bantları model skorlarını izleme katmanına çeviriyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Gözlenen sahtecilik oranı (%)")
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
    ax.text(0.02, baseline * 100 + 0.25, f"Baz oran {baseline * 100:.2f}%", color=COLORS["ink"], fontsize=9)
    ax.set_title("Product C ana risk ayrışmasıdır", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Sahtecilik oranı (%)")
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
            case when has_identity = 1 then 'Identity var' else 'Identity kaydı yok' end as identity_status,
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
    ax.set_title("Identity kaydı risk sinyalidir; yalnızca veri tamlığı değildir", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Sahtecilik oranı (%)")
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
    ax.set_title("Kredi kartı kombinasyonlarında risk daha yüksek", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label="Sahtecilik oranı (%)")
    ax.spines[:].set_visible(False)
    savefig(CHART_DIR / "12_card_payment_heatmap.png")


def chart_email_risk(con: duckdb.DuckDBPyConnection, baseline: float) -> None:
    df = read(con, "select * from mart.mart_email_domain_stats order by fraud_rate desc")
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.barh(df["purchaser_email_group"][::-1], df["fraud_rate"][::-1] * 100, color=COLORS["blue"])
    ax.axvline(baseline * 100, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_title("Email domain grupları operasyonel risk segmentleri oluşturuyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("Sahtecilik oranı (%)")
    ax.grid(axis="x", color=COLORS["grid"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    savefig(CHART_DIR / "13_email_domain_risk.png")


def chart_amount_distribution(con: duckdb.DuckDBPyConnection) -> None:
    df = read(
        con,
        """
        select
            case when is_fraud = 1 then 'Sahtecilik' else 'Normal' end as label,
            transaction_amount
        from intermediate.int_features
        where transaction_amount between 0 and 1500
        """,
    )
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    legit = df[df["label"].eq("Normal")]["transaction_amount"]
    fraud = df[df["label"].eq("Sahtecilik")]["transaction_amount"]
    ax.hist(legit, bins=80, alpha=0.45, density=True, color=COLORS["teal"], label="Normal")
    ax.hist(fraud, bins=80, alpha=0.55, density=True, color=COLORS["red"], label="Sahtecilik")
    ax.set_title("Sahtecilik tutar dağılımı uçlarda yoğunlaşıyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_xlabel("İşlem tutarı, $1.500 üst sınır")
    ax.set_ylabel("Yoğunluk")
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
    ax1.set_ylabel("Sahtecilik oranı (%)", color=COLORS["red"])
    ax1.tick_params(axis="y", labelcolor=COLORS["red"])
    ax1.set_xticks(range(0, 24, 2))
    ax1.grid(axis="y", color=COLORS["grid"])
    ax2 = ax1.twinx()
    ax2.bar(df["transaction_hour"], df["transaction_count"], color=COLORS["blue"], alpha=0.18, width=0.8)
    ax2.set_ylabel("İşlem sayısı", color=COLORS["blue"])
    ax2.tick_params(axis="y", labelcolor=COLORS["blue"])
    ax1.set_title("Gün içi örüntü izleme bağlamı sağlar", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax1.set_xlabel("TransactionDT'ye göre göreli saat")
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.spines[["top", "left"]].set_visible(False)
    savefig(CHART_DIR / "15_hourly_pattern.png")


def chart_risk_lift(risk: pd.DataFrame, baseline: float) -> None:
    df = risk[risk["split"].eq("train")].copy()
    order = ["Low", "Elevated", "High", "Critical"]
    df["risk_band"] = pd.Categorical(df["risk_band"], categories=order, ordered=True)
    df = df.sort_values("risk_band")
    df["lift"] = df["observed_fraud_rate"] / baseline
    label_map = {"Low": "Düşük", "Elevated": "Yükselen", "High": "Yüksek", "Critical": "Kritik"}
    df["risk_band_tr"] = df["risk_band"].astype(str).map(label_map)
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.bar(df["risk_band_tr"], df["lift"], color=[COLORS["teal"], COLORS["amber"], COLORS["violet"], COLORS["red"]])
    ax.axhline(1, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_title("Model risk bantları ölçülebilir inceleme kuyrukları oluşturuyor", loc="left", fontsize=15, weight="bold", color=COLORS["ink"])
    ax.set_ylabel("Baz orana göre risk çarpanı")
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

    headers = [("VERİ ALIMI", 1.0), ("DEPOLAMA", 3.6), ("DÖNÜŞÜM", 6.1), ("MODEL", 3.6), ("GÖRSELLEŞTİRME", 9.2)]
    for text, x in headers:
        ax.text(x, 6.45, text, fontsize=10.5, weight="bold", color=COLORS["muted"], ha="center")
    ax.plot([0.5, 11.5], [6.25, 6.25], color=COLORS["grid"], linewidth=1)

    box(0.5, 5.0, 2.1, 0.75, "Kaggle CSV", "train/test işlem + identity", COLORS["teal"])
    box(3.1, 5.0, 2.1, 0.75, "BigQuery", "ham veri tabloları", COLORS["blue"])
    box(5.8, 5.0, 2.1, 0.75, "dbt Core", "staging + intermediate + mart", COLORS["violet"])
    box(8.9, 5.0, 2.1, 0.75, "Power BI", "yönetici raporu", COLORS["amber"])
    arrow(2.6, 5.38, 3.1, 5.38)
    arrow(5.2, 5.38, 5.8, 5.38)
    arrow(7.9, 5.38, 8.9, 5.38)

    box(3.1, 3.6, 2.1, 0.75, "DuckDB", "tekrarlanabilir analitik depo", COLORS["green"])
    box(5.8, 3.6, 2.1, 0.75, "Mart Katmanı", "günlük, segment, risk, model tabloları", COLORS["violet"])
    box(8.9, 3.6, 2.1, 0.75, "Looker Studio", "alternatif raporlama görünümü", COLORS["red"])
    arrow(1.55, 5.0, 4.15, 4.35, dashed=True)
    arrow(5.2, 3.98, 5.8, 3.98)
    arrow(7.9, 3.98, 8.9, 3.98)

    box(0.5, 2.0, 2.1, 0.75, "Python / Model", "LightGBM + doğrulama", "#3F3F46")
    box(3.1, 2.0, 2.1, 0.75, "Model Skorları", "olasılık + risk bantları", COLORS["blue"])
    arrow(2.6, 2.38, 3.1, 2.38)
    arrow(5.2, 2.38, 6.5, 3.6, dashed=True)

    box(0.6, 0.55, 2.35, 0.65, "staging", "tip dönüşümü + temizlik", COLORS["teal"])
    box(3.55, 0.55, 2.35, 0.65, "intermediate", "join + feature üretimi", COLORS["blue"])
    box(6.5, 0.55, 2.35, 0.65, "mart", "sahtecilik metrikleri", COLORS["violet"])
    box(9.45, 0.55, 1.6, 0.65, "test", "kalite kontrolleri", COLORS["amber"])
    arrow(2.95, 0.88, 3.55, 0.88)
    arrow(5.9, 0.88, 6.5, 0.88)
    arrow(8.85, 0.88, 9.45, 0.88)
    ax.text(6, 1.55, "DBT KATMANLARI", fontsize=10.5, weight="bold", color=COLORS["muted"], ha="center")
    savefig(CHART_DIR / "09_architecture.png")


def write_docs(summary: pd.DataFrame, metrics: dict) -> None:
    row = summary.iloc[0]
    executive = f"""# IEEE-CIS Fraud Detection Yönetici Özeti

## Temel Metrikler

- Toplam işlem: {int(row['total_transactions']):,}
- Sahtecilik etiketi taşıyan işlem: {int(row['fraud_transactions']):,}
- Sahtecilik oranı: {pct(row['fraud_rate'])}
- Identity kapsama oranı: {pct(row['identity_coverage_rate'])}
- Medyan işlem tutarı: ${row['median_transaction_amount']:,.2f}
- P95 işlem tutarı: ${row['p95_transaction_amount']:,.2f}
- Doğrulama AUC: {metrics['ml']['validation_auc']:.3f}
- Doğrulama average precision: {metrics['ml']['validation_average_precision']:.3f}

## Yönetici Çıkarımı

Veri seti, nadir görülen ancak belirli segmentlerde yoğunlaşan bir sahtecilik problemidir. Risk; ürün ailesi, identity kaydı, ödeme tipi, email domain, işlem tutarı ve zaman penceresine göre belirgin biçimde ayrışır. Önerilen analitik model; ham veri katmanı, dbt dönüşümleri, LightGBM skorlaması ve Power BI için hazırlanmış mart tablolarından oluşur.
"""
    (TABLES_DIR / "executive_summary.md").write_text(executive, encoding="utf-8")

    dashboard = """# Power BI Rapor Spesifikasyonu

## Veri Kaynakları

`outputs/powerbi/` klasöründeki tüm CSV dosyalarını içe aktarın.

## İlişkiler

- `fact_train_transactions[transaction_id]` alanını `mart_model_predictions[transaction_id]` alanına bağlayın.
- Performans ihtiyacında `mart_daily_stats`, `mart_amount_bands`, `mart_product_device_stats` ve `mart_risk_band_stats` tablolarını özet sayfalarda kullanın.

## Ölçüler

```DAX
Transactions = COUNTROWS(fact_train_transactions)
Fraud Transactions = SUM(fact_train_transactions[is_fraud])
Fraud Rate = DIVIDE([Fraud Transactions], [Transactions])
Average Amount = AVERAGE(fact_train_transactions[transaction_amount])
Predicted Risk = AVERAGE(fact_train_transactions[predicted_fraud_probability])
High Risk Transactions =
CALCULATE([Transactions], fact_train_transactions[risk_band] IN {"High", "Critical"})
```

## Sayfalar

1. Yönetici Özeti: baz sahtecilik oranı, Product C lift, identity lift ve risk bandı lift analizi.
2. Ürün ve Identity: ürün seviyesinde risk yoğunlaşması ve identity kaydı olan/olmayan işlemler.
3. Ödeme ve Email: kart ağı/tipi heatmap'i ve email domain risk grupları.
4. Tutar ve Zaman: tutar bandı riski, tutar dağılımı, günlük drift ve saatlik örüntü.
5. Model Riski: feature importance, zamana dayalı ROC, risk bantları ve bant bazında gözlenen sahtecilik.
6. Veri Kalitesi: yapısal eksiklik, identity kapsama oranı, dbt test durumu ve mimari bağlam.

## Anlatı

Sunumu "sahtecilik nerede yoğunlaşıyor?" sorusuyla başlatın. Rapor; ürün, identity, ödeme, email, tutar ve zaman kırılımlarında sahteciliğin rastgele dağılmadığını göstermelidir. Model skorları, segment analizinden sonra gelen operasyonel önceliklendirme katmanı olarak konumlandırılmalıdır.
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
    story = f"""# Analiz Hikayesi

## Ana Soru

Sahtecilik hangi segmentlerde yoğunlaşıyor ve BI ekibi bunu nasıl izlemeli?

## Temel Bulgular

1. Sahtecilik nadir ancak yoğunlaşmış durumda: baz oran {pct(row['fraud_rate'])}.
2. Ürün riski eşit dağılmıyor: Product C sahtecilik oranı {product.iloc[0]['fraud_rate'] * 100:.2f}%, Product W ise {product[product['product_cd'].eq('W')].iloc[0]['fraud_rate'] * 100:.2f}%.
3. Identity kaydı risk sinyalidir: identity kaydı olan işlemlerde oran {identity[identity['has_identity'].eq(1)].iloc[0]['fraud_rate'] * 100:.2f}%, olmayan işlemlerde {identity[identity['has_identity'].eq(0)].iloc[0]['fraud_rate'] * 100:.2f}%.
4. Tutar riski doğrusal değildir: <$25 ve $250+ bantları orta tutarlı işlemlere göre daha yüksek risk taşır.
5. Ödeme özellikleri ayrıştırıcıdır: kredi kartı kombinasyonları debit kart kombinasyonlarına göre daha yüksek risk gösterir.
6. Model, izleme ve önceliklendirme katmanı olarak kullanılmalıdır: Kritik risk bandı baz orana göre çok yüksek lift üretir.

## Önerilen Sunum Akışı

Önce sınıf dengesizliğini gösterin, ardından sahteciliğin rastgele dağılmadığını kanıtlayın. Ürün, identity, tutar, ödeme, email ve zaman kırılımlarıyla ilerleyin. Son bölümde model risk bantlarını nihai karar mekanizması olarak değil, operasyonel önceliklendirme katmanı olarak konumlandırın.
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
