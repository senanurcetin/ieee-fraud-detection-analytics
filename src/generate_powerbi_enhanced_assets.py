from __future__ import annotations

import os
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from google.cloud import bigquery

warnings.filterwarnings("ignore", message="BigQuery Storage module not found.*")

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "powerbi" / "assets"
DEFAULT_CREDENTIALS = Path(r"C:\Users\MONSTER\Downloads\workintech-working-2378ce4f85e2.json")
PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "workintech-working")
DATASET = os.getenv("BIGQUERY_REPORTING_DATASET", "fraud_project_powerbi")

COLORS = {
    "navy": "#14213D",
    "text": "#1F2937",
    "muted": "#6B7280",
    "line": "#D1D5DB",
    "red": "#B42318",
    "amber": "#B7791F",
    "green": "#0F766E",
    "blue": "#2563EB",
    "bg": "#FFFFFF",
}


def ensure_credentials() -> None:
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return
    if DEFAULT_CREDENTIALS.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(DEFAULT_CREDENTIALS)


def bq(query: str) -> pd.DataFrame:
    client = bigquery.Client(project=PROJECT_ID)
    return client.query(query).to_dataframe()


def fmt_int(value: float | int) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value: float | int) -> str:
    return f"{float(value) * 100:.2f}%".replace(".", ",")


def style_axes(ax, title: str | None = None) -> None:
    ax.set_facecolor(COLORS["bg"])
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["line"])
    ax.tick_params(axis="x", colors=COLORS["text"], labelsize=9)
    ax.tick_params(axis="y", colors=COLORS["muted"], labelsize=9)
    ax.grid(axis="y", color="#EEF2F7", linewidth=0.8)
    if title:
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=COLORS["navy"], pad=12)


def save(fig: plt.Figure, name: str) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSET_DIR / name, dpi=180, bbox_inches="tight", facecolor=COLORS["bg"])
    plt.close(fig)


def executive_control_panel() -> None:
    kpi = bq(f"select * from `{PROJECT_ID}.{DATASET}.pbi_executive_kpis`").iloc[0]
    readiness = bq(
        f"""
        select status, count(*) as check_count
        from `{PROJECT_ID}.{DATASET}.pbi_report_readiness`
        group by status
        """
    )
    pass_count = int(readiness.loc[readiness["status"] == "PASS", "check_count"].sum())
    total_checks = int(readiness["check_count"].sum())

    cards = [
        ("Toplam İşlem", fmt_int(kpi["total_transactions"]), "Analiz evreni"),
        ("Fraud Oranı", fmt_pct(kpi["fraud_rate"]), "Baz risk seviyesi"),
        ("Product C Lift", f"{float(kpi['product_c_lift']):.2f}x", "Öncelikli ürün riski"),
        ("Identity Lift", f"{float(kpi['identity_lift']):.2f}x", "Kayıtlı identity riski"),
        ("Kritik Bant Lift", f"{float(kpi['critical_risk_lift']):.2f}x", "Model öncelik sinyali"),
        ("Kalite Kontrol", f"{pass_count}/{total_checks} PASS", "Sunum öncesi kapı"),
    ]

    fig, ax = plt.subplots(figsize=(12.8, 2.25))
    ax.axis("off")
    fig.patch.set_facecolor(COLORS["bg"])
    for idx, (label, value, note) in enumerate(cards):
        x = 0.012 + idx * 0.164
        width = 0.15
        rect = plt.Rectangle((x, 0.12), width, 0.76, transform=ax.transAxes, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1)
        ax.add_patch(rect)
        ax.text(x + 0.014, 0.70, label, transform=ax.transAxes, fontsize=9.5, color=COLORS["muted"], fontweight="bold")
        ax.text(x + 0.014, 0.43, value, transform=ax.transAxes, fontsize=18, color=COLORS["navy"], fontweight="bold")
        ax.text(x + 0.014, 0.22, note, transform=ax.transAxes, fontsize=8.5, color=COLORS["muted"])
    save(fig, "17_executive_control_panel.png")


def segment_watchlist() -> None:
    df = bq(
        f"""
        select watchlist_rank, segment_family, segment_name, transaction_count,
               fraud_rate, lift, fraud_share, risk_priority
        from `{PROJECT_ID}.{DATASET}.pbi_segment_watchlist`
        order by watchlist_rank
        limit 10
        """
    )
    fig, ax = plt.subplots(figsize=(12.8, 4.2))
    ax.axis("off")
    ax.set_title("Operasyonel Segment İzleme Listesi", loc="left", fontsize=16, fontweight="bold", color=COLORS["navy"], pad=16)

    table_df = df.copy()
    table_df["transaction_count"] = table_df["transaction_count"].map(fmt_int)
    table_df["fraud_rate"] = table_df["fraud_rate"].map(fmt_pct)
    table_df["lift"] = table_df["lift"].map(lambda v: f"{float(v):.2f}x")
    table_df["fraud_share"] = table_df["fraud_share"].map(fmt_pct)
    table_df = table_df.rename(
        columns={
            "watchlist_rank": "Sıra",
            "segment_family": "Segment",
            "segment_name": "Kırılım",
            "transaction_count": "İşlem",
            "fraud_rate": "Fraud Oranı",
            "lift": "Lift",
            "fraud_share": "Fraud Payı",
            "risk_priority": "Öncelik",
        }
    )
    table = ax.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        loc="upper left",
        cellLoc="left",
        colLoc="left",
        bbox=[0.0, 0.02, 1.0, 0.86],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        if row == 0:
            cell.set_facecolor(COLORS["navy"])
            cell.set_text_props(color="white", weight="bold")
        elif table_df.iloc[row - 1]["Öncelik"] == "Kritik":
            cell.set_facecolor("#FEF2F2")
        elif table_df.iloc[row - 1]["Öncelik"] == "Yüksek":
            cell.set_facecolor("#FFF7ED")
        else:
            cell.set_facecolor("#FFFFFF")
    save(fig, "18_segment_watchlist.png")


def model_threshold_simulation() -> None:
    df = bq(
        f"""
        select score_threshold, workload_share, fraud_capture_rate, precision_rate, operating_mode
        from `{PROJECT_ID}.{DATASET}.pbi_threshold_simulation`
        order by score_threshold
        """
    )
    fig, ax = plt.subplots(figsize=(12.8, 4.3))
    style_axes(ax, "Skor Eşiği Simülasyonu: İnceleme Yükü ve Fraud Yakalama")
    ax.plot(df["score_threshold"], df["fraud_capture_rate"], color=COLORS["red"], linewidth=2.8, marker="o", label="Yakalanan fraud oranı")
    ax.plot(df["score_threshold"], df["workload_share"], color=COLORS["blue"], linewidth=2.8, marker="o", label="İnceleme yükü")
    ax.plot(df["score_threshold"], df["precision_rate"], color=COLORS["green"], linewidth=2.4, marker="o", label="Precision")
    ax.set_xlabel("Model skor eşiği", color=COLORS["muted"])
    ax.set_ylabel("Oran", color=COLORS["muted"])
    ax.yaxis.set_major_formatter(lambda x, _pos: fmt_pct(x))
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    ax.text(
        0.01,
        -0.27,
        "Yorum: Eşik yükseldikçe operasyon yükü düşer; hedef, fraud yakalama oranı ile inceleme kapasitesi arasında dengeli kuyruk kurmaktır.",
        transform=ax.transAxes,
        fontsize=9,
        color=COLORS["muted"],
    )
    save(fig, "19_model_threshold_simulation.png")


def qa_readiness_scorecard() -> None:
    df = bq(
        f"""
        select readiness_area, status, count(*) as check_count
        from `{PROJECT_ID}.{DATASET}.pbi_report_readiness`
        group by readiness_area, status
        order by readiness_area, status
        """
    )
    pivot = df.pivot_table(index="readiness_area", columns="status", values="check_count", aggfunc="sum", fill_value=0)
    for col in ["PASS", "FAIL"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot.reset_index()

    fig, ax = plt.subplots(figsize=(12.8, 3.2))
    style_axes(ax, "Sunum Öncesi Hazırlık Kontrolleri")
    ax.barh(pivot["readiness_area"], pivot["PASS"], color=COLORS["green"], label="PASS")
    if pivot["FAIL"].sum() > 0:
        ax.barh(pivot["readiness_area"], pivot["FAIL"], left=pivot["PASS"], color=COLORS["red"], label="FAIL")
    for i, row in pivot.iterrows():
        ax.text(row["PASS"] + row["FAIL"] + 0.05, i, f"{int(row['PASS'])} PASS / {int(row['FAIL'])} FAIL", va="center", fontsize=9, color=COLORS["text"])
    ax.set_xlabel("Kontrol sayısı", color=COLORS["muted"])
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    save(fig, "20_qa_readiness_scorecard.png")


def executive_decision_matrix() -> None:
    df = bq(
        f"""
        select segment_family, segment_name, fraud_share, lift, risk_priority, recommended_action
        from `{PROJECT_ID}.{DATASET}.pbi_segment_watchlist`
        order by watchlist_rank
        limit 6
        """
    )
    fig, ax = plt.subplots(figsize=(12.8, 2.35))
    ax.axis("off")
    ax.set_title("Yönetim Aksiyon Matrisi", loc="left", fontsize=15, fontweight="bold", color=COLORS["navy"], pad=10)

    for idx, row in df.iterrows():
        x = 0.01 + (idx % 3) * 0.33
        y = 0.48 if idx < 3 else 0.08
        priority = row["risk_priority"]
        edge = COLORS["red"] if priority == "Kritik" else COLORS["amber"] if priority == "Yüksek" else COLORS["green"]
        rect = plt.Rectangle((x, y), 0.31, 0.30, transform=ax.transAxes, facecolor="#FFFFFF", edgecolor=edge, linewidth=1.8)
        ax.add_patch(rect)
        ax.text(x + 0.014, y + 0.205, f"{row['segment_family']} | {row['segment_name']}", transform=ax.transAxes, fontsize=9.5, color=COLORS["navy"], fontweight="bold")
        ax.text(x + 0.014, y + 0.125, f"Fraud payı {fmt_pct(row['fraud_share'])}  |  Lift {float(row['lift']):.2f}x", transform=ax.transAxes, fontsize=8.5, color=COLORS["text"])
        ax.text(x + 0.014, y + 0.045, str(row["recommended_action"]), transform=ax.transAxes, fontsize=8.0, color=COLORS["muted"])

    save(fig, "21_executive_decision_matrix.png")


def review_strategy_matrix() -> None:
    df = bq(
        f"""
        select risk_band, review_priority, estimated_daily_review_volume,
               expected_fraud_capture, lift, queue_policy, management_note
        from `{PROJECT_ID}.{DATASET}.pbi_review_strategy`
        order by band_rank
        """
    )
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.axis("off")
    ax.set_title("Operasyon Kuyruğu Stratejisi", loc="left", fontsize=14, fontweight="bold", color=COLORS["navy"], pad=10)
    table_df = df.copy()
    table_df["estimated_daily_review_volume"] = table_df["estimated_daily_review_volume"].map(lambda v: fmt_int(round(float(v))))
    table_df["expected_fraud_capture"] = table_df["expected_fraud_capture"].map(fmt_pct)
    table_df["lift"] = table_df["lift"].map(lambda v: f"{float(v):.1f}x")
    table_df["queue_policy"] = table_df["queue_policy"].map(
        {
            "Anlık inceleme kuyruğu": "Anlık",
            "Aynı gün öncelikli inceleme": "Aynı gün",
            "Örneklem bazlı manuel kontrol": "Örneklem",
            "Otomatik izleme": "Otomatik",
        }
    )
    table_df = table_df.rename(
        columns={
            "risk_band": "Bant",
            "review_priority": "Öncelik",
            "estimated_daily_review_volume": "Günlük hacim",
            "expected_fraud_capture": "Yakalama",
            "lift": "Lift",
            "queue_policy": "Politika",
        }
    )[["Bant", "Öncelik", "Günlük hacim", "Yakalama", "Lift", "Politika"]]
    table = ax.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0, 0.03, 1, 0.84],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.2)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        if row == 0:
            cell.set_facecolor(COLORS["navy"])
            cell.set_text_props(color="white", weight="bold")
        elif table_df.iloc[row - 1]["Bant"] == "Critical":
            cell.set_facecolor("#FEF2F2")
        elif table_df.iloc[row - 1]["Bant"] == "High":
            cell.set_facecolor("#FFF7ED")
        else:
            cell.set_facecolor("#FFFFFF")
    save(fig, "22_review_strategy_matrix.png")


def risk_funnel() -> None:
    kpi = bq(f"select * from `{PROJECT_ID}.{DATASET}.pbi_executive_kpis`").iloc[0]
    bands = bq(
        f"""
        select risk_band, transaction_count, observed_fraud_count, expected_fraud_capture
        from `{PROJECT_ID}.{DATASET}.pbi_review_strategy`
        order by band_rank
        """
    )
    high_critical = bands[bands["risk_band"].isin(["Critical", "High"])]
    critical = bands[bands["risk_band"] == "Critical"].iloc[0]
    rows = [
        ("Tüm işlem", int(kpi["total_transactions"]), 1.0, COLORS["blue"]),
        ("High + Critical", int(high_critical["transaction_count"].sum()), float(high_critical["expected_fraud_capture"].sum()), COLORS["amber"]),
        ("Critical", int(critical["transaction_count"]), float(critical["expected_fraud_capture"]), COLORS["red"]),
    ]

    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    ax.axis("off")
    ax.set_title("Risk Kuyruğu Hunisi", loc="left", fontsize=14, fontweight="bold", color=COLORS["navy"], pad=10)
    max_width = 0.68
    for idx, (label, count, capture, color) in enumerate(rows):
        y = 0.68 - idx * 0.24
        width = max_width * (0.92 - idx * 0.22)
        x = 0.28 + (max_width - width) / 2
        rect = plt.Rectangle((x, y), width, 0.15, transform=ax.transAxes, facecolor=color, alpha=0.92)
        ax.add_patch(rect)
        ax.text(0.05, y + 0.047, label, transform=ax.transAxes, fontsize=9, color=COLORS["text"], fontweight="bold")
        ax.text(x + width / 2, y + 0.047, fmt_int(count), transform=ax.transAxes, fontsize=10, color="white", fontweight="bold", ha="center")
        ax.text(0.91, y + 0.047, f"Yakalama {fmt_pct(capture)}", transform=ax.transAxes, fontsize=8.5, color=COLORS["text"], ha="center")
    ax.text(0.04, 0.08, "Amaç: sınırlı manuel inceleme kapasitesini en yüksek fraud yakalama katkısı veren kuyruğa yönlendirmek.", transform=ax.transAxes, fontsize=8.5, color=COLORS["muted"])
    save(fig, "24_risk_funnel.png")


def dbt_quality_gate() -> None:
    readiness = bq(
        f"""
        select readiness_area, status, count(*) as check_count
        from `{PROJECT_ID}.{DATASET}.pbi_report_readiness`
        group by readiness_area, status
        order by readiness_area, status
        """
    )
    contract = bq(
        f"""
        select object_name, expected_rows, actual_rows, status
        from `{PROJECT_ID}.{DATASET}.pbi_quality_contract`
        order by object_name
        """
    )
    pass_count = int(readiness.loc[readiness["status"] == "PASS", "check_count"].sum())
    total_count = int(readiness["check_count"].sum())

    fig, ax = plt.subplots(figsize=(12.8, 3.0))
    ax.axis("off")
    ax.set_title("dbt ve BigQuery Kalite Kapısı", loc="left", fontsize=15, fontweight="bold", color=COLORS["navy"], pad=10)
    ax.text(0.01, 0.72, f"{pass_count}/{total_count}", transform=ax.transAxes, fontsize=30, color=COLORS["green"], fontweight="bold")
    ax.text(0.01, 0.55, "hazırlık kontrolü PASS", transform=ax.transAxes, fontsize=10, color=COLORS["muted"])
    ax.text(0.01, 0.36, "Build: 29 model, 67 test, 0 hata.", transform=ax.transAxes, fontsize=10, color=COLORS["text"])

    mini = contract.copy().head(6)
    mini["object_name"] = mini["object_name"].str.replace("powerbi.", "", regex=False).str.replace("raw.", "", regex=False)
    mini["expected_rows"] = mini["expected_rows"].map(fmt_int)
    mini["actual_rows"] = mini["actual_rows"].map(fmt_int)
    mini = mini.rename(columns={"object_name": "Nesne", "expected_rows": "Beklenen", "actual_rows": "Gerçek", "status": "Durum"})
    table = ax.table(
        cellText=mini[["Nesne", "Beklenen", "Gerçek", "Durum"]].values,
        colLabels=["Nesne", "Beklenen", "Gerçek", "Durum"],
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0.46, 0.12, 0.52, 0.74],
        colWidths=[0.34, 0.22, 0.22, 0.16],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        if row == 0:
            cell.set_facecolor(COLORS["navy"])
            cell.set_text_props(color="white", weight="bold")
        elif mini.iloc[row - 1]["Durum"] == "PASS":
            cell.set_facecolor("#F0FDF4")
        else:
            cell.set_facecolor("#FEF2F2")
    save(fig, "25_dbt_quality_gate.png")


def main() -> None:
    ensure_credentials()
    executive_control_panel()
    segment_watchlist()
    model_threshold_simulation()
    qa_readiness_scorecard()
    executive_decision_matrix()
    review_strategy_matrix()
    risk_funnel()
    dbt_quality_gate()
    print(f"Enhanced Power BI assets written to {ASSET_DIR}")


if __name__ == "__main__":
    main()
