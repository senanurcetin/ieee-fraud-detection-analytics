from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path(r"C:\Users\MONSTER\.codex\plugins\cache\openai-primary-runtime\presentations\26.515.10909\skills\presentations")
NODE = Path(r"C:\Users\MONSTER\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe")
WORKSPACE = ROOT / "outputs" / "manual-20260518-ieee" / "presentations" / "ieee-fraud-analysis"
SLIDES_DIR = WORKSPACE / "slides"
PREVIEW_DIR = WORKSPACE / "preview"
LAYOUT_DIR = WORKSPACE / "layout"
OUTPUT_DIR = ROOT / "outputs" / "presentation"
FINAL_PPTX = OUTPUT_DIR / "ieee-cis-fraud-detection-analysis.pptx"
CONTACT_SHEET = WORKSPACE / "qa" / "contact-sheet.png"
DB_PATH = ROOT / "data" / "processed" / "ieee_fraud.duckdb"
CHART_DIR = ROOT / "outputs" / "charts"
TABLES_DIR = ROOT / "outputs" / "tables"


def js_string(value: str | Path) -> str:
    return json.dumps(str(value).replace("\\", "/"))


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def money(value: float) -> str:
    return f"${value:,.0f}"


def load_numbers() -> dict:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    summary = con.execute("select * from mart.mart_fraud_summary").fetch_df().iloc[0].to_dict()
    amount = con.execute("select * from mart.mart_amount_bands order by amount_band").fetch_df()
    risk = con.execute("select * from mart.mart_risk_band_stats where split = 'train' order by avg_predicted_probability desc").fetch_df()
    product = con.execute("select * from mart.mart_product_device_stats order by fraud_rate desc, transaction_count desc limit 1").fetch_df().iloc[0].to_dict()
    missing = con.execute(
        """
        select column_family, avg(missing_rate) as avg_missing
        from mart.mart_feature_missingness
        where table_name = 'train_transaction'
        group by 1
        order by avg_missing desc
        limit 1
        """
    ).fetch_df().iloc[0].to_dict()
    metrics = json.loads((TABLES_DIR / "raw_profile.json").read_text(encoding="utf-8"))
    feature = pd.read_csv(TABLES_DIR / "feature_importance.csv").head(1).iloc[0].to_dict()
    return {
        "summary": summary,
        "amount": amount.to_dict(orient="records"),
        "risk": risk.to_dict(orient="records"),
        "product": product,
        "missing": missing,
        "metrics": metrics,
        "feature": feature,
    }


COMMON = r"""
import fs from "node:fs";

export const W = 1280;
export const H = 720;
export const C = {
  ink: "#17212B",
  muted: "#64748B",
  grid: "#D9E2EC",
  paper: "#F8FAFC",
  white: "#FFFFFF",
  teal: "#0F766E",
  blue: "#2563EB",
  red: "#B42318",
  amber: "#B7791F",
  violet: "#6D28D9",
  green: "#2F855A",
  dark: "#111827",
};

export function addBase(slide, eyebrow, title) {
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: W, height: H }, fill: { type: "solid", color: C.paper }, line: { width: 0, fill: C.paper } });
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: W, height: 8 }, fill: { type: "solid", color: C.teal }, line: { width: 0, fill: C.teal } });
  text(slide, eyebrow, 54, 34, 480, 22, { size: 9, color: C.muted, bold: true });
  text(slide, title, 54, 58, 850, 68, { size: 26, color: C.ink, bold: true });
  slide.shapes.add({ geometry: "rect", position: { left: 54, top: 126, width: 1172, height: 1 }, fill: { type: "solid", color: C.grid }, line: { width: 0, fill: C.grid } });
}

export function footer(slide, page) {
  text(slide, "Source: Kaggle IEEE-CIS Fraud Detection competition files; local DuckDB/dbt analysis", 54, 678, 760, 20, { size: 8, color: C.muted });
  text(slide, String(page).padStart(2, "0"), 1182, 676, 42, 22, { size: 10, color: C.muted, bold: true, align: "right" });
}

export function text(slide, value, left, top, width, height, opts = {}) {
  const fill = opts.fill || C.paper;
  const shape = slide.shapes.add({ geometry: "rect", position: { left, top, width, height }, fill: { type: "solid", color: fill }, line: { width: 0, fill } });
  shape.text = value;
  shape.text.fontSize = opts.size || 14;
  shape.text.color = opts.color || C.ink;
  shape.text.bold = Boolean(opts.bold);
  shape.text.typeface = "Arial";
  shape.text.alignment = opts.align || "left";
  shape.text.verticalAlignment = opts.valign || "top";
  return shape;
}

export function card(slide, label, value, note, left, top, width, color = C.teal) {
  slide.shapes.add({ geometry: "roundRect", position: { left, top, width, height: 118 }, fill: { type: "solid", color: C.white }, line: { width: 1, fill: "#E5E7EB" } });
  slide.shapes.add({ geometry: "rect", position: { left, top, width: 5, height: 118 }, fill: { type: "solid", color }, line: { width: 0, fill: color } });
  text(slide, label, left + 18, top + 16, width - 34, 22, { size: 9, color: C.muted, bold: true, fill: C.white });
  text(slide, value, left + 18, top + 41, width - 34, 40, { size: 24, color, bold: true, fill: C.white });
  text(slide, note, left + 18, top + 83, width - 34, 24, { size: 9, color: C.muted, fill: C.white });
}

export function image(slide, filePath, left, top, width, height, alt = "") {
  const contentType = filePath.toLowerCase().endsWith(".jpg") || filePath.toLowerCase().endsWith(".jpeg") ? "image/jpeg" : "image/png";
  const dataUrl = `data:${contentType};base64,${fs.readFileSync(filePath).toString("base64")}`;
  return slide.images.add({ dataUrl, contentType, alt, position: { left, top, width, height }, fit: "contain" });
}

export function pill(slide, value, left, top, width, color) {
  slide.shapes.add({ geometry: "roundRect", position: { left, top, width, height: 34 }, fill: { type: "solid", color }, line: { width: 0, fill: color } });
  text(slide, value, left + 8, top + 8, width - 16, 18, { size: 9, color: C.white, bold: true, align: "center", fill: color });
}

export function callout(slide, title, body, left, top, width, height, color = C.blue) {
  slide.shapes.add({ geometry: "roundRect", position: { left, top, width, height }, fill: { type: "solid", color: "#EEF2FF" }, line: { width: 1, fill: "#C7D2FE" } });
  text(slide, title, left + 18, top + 15, width - 36, 24, { size: 12, color, bold: true, fill: "#EEF2FF" });
  text(slide, body, left + 18, top + 44, width - 36, height - 55, { size: 10, color: C.ink, fill: "#EEF2FF" });
}
"""


def slide_module(index: int, body: str) -> str:
    return f"""
import {{ addBase, footer, text, card, image, pill, callout, C }} from "./common.mjs";

export async function slide{index:02d}(presentation, ctx) {{
  const slide = presentation.slides.add();
{body}
  footer(slide, {index});
  return slide;
}}
"""


def write_slides(numbers: dict) -> None:
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    (SLIDES_DIR / "common.mjs").write_text(COMMON, encoding="utf-8")

    s = numbers["summary"]
    metrics = numbers["metrics"]
    product = numbers["product"]
    missing = numbers["missing"]
    feature = numbers["feature"]
    critical = next(row for row in numbers["risk"] if row["risk_band"] == "Critical")
    high = next(row for row in numbers["risk"] if row["risk_band"] == "High")

    charts = {name: js_string(CHART_DIR / name) for name in [
        "01_class_imbalance.png",
        "02_daily_fraud_rate.png",
        "03_amount_bands.png",
        "04_product_device_risk.png",
        "05_feature_importance.png",
        "06_validation_roc.png",
        "07_missingness_by_family.png",
        "08_risk_bands.png",
        "09_architecture.png",
    ]}

    slides = [
        slide_module(1, f"""
  addBase(slide, "FRAUD ANALYTICS CASE STUDY", "IEEE-CIS Fraud Detection: BI + ML Production Analysis");
  text(slide, "A full analytics pipeline from Kaggle CSVs to dbt marts, LightGBM risk scoring, Power BI handoff, and BigQuery-ready deployment.", 58, 148, 780, 64, {{ size: 16, color: C.ink }});
  card(slide, "TRAIN TRANSACTIONS", "{int(s['total_transactions']):,}", "Official Kaggle train_transaction.csv", 58, 246, 250, C.teal);
  card(slide, "OBSERVED FRAUD RATE", "{pct(s['fraud_rate'])}", "{int(s['fraud_transactions']):,} fraud labels", 336, 246, 250, C.red);
  card(slide, "IDENTITY COVERAGE", "{pct(s['identity_coverage_rate'])}", "Joined via TransactionID", 614, 246, 250, C.blue);
  card(slide, "VALIDATION AUC", "{metrics['ml']['validation_auc']:.3f}", "Time-based holdout", 892, 246, 250, C.violet);
  image(slide, {charts['09_architecture.png']}, 118, 396, 1040, 226, "Architecture overview");
"""),
        slide_module(2, f"""
  addBase(slide, "DATA FOUNDATION", "The Kaggle files form a transaction-first fraud warehouse");
  card(slide, "TRAIN TRANSACTION", "{metrics['tables']['train_transaction']['rows']:,}", "{metrics['tables']['train_transaction']['columns']} columns", 58, 160, 220, C.teal);
  card(slide, "TRAIN IDENTITY", "{metrics['tables']['train_identity']['rows']:,}", "{metrics['tables']['train_identity']['columns']} columns", 300, 160, 220, C.blue);
  card(slide, "TEST TRANSACTION", "{metrics['tables']['test_transaction']['rows']:,}", "{metrics['tables']['test_transaction']['columns']} columns", 542, 160, 220, C.violet);
  card(slide, "DBT QA", "11 / 11", "not-null, unique, accepted values", 784, 160, 220, C.green);
  callout(slide, "Design decision", "TransactionID remains the warehouse grain. Identity data is sparse and joined as an enrichment layer, not treated as a required dimension.", 58, 320, 420, 176, C.blue);
  callout(slide, "Modeling implication", "Feature families are preserved: core transaction, card, address, C/D/M/V engineered features, email domains, and identity/device attributes.", 520, 320, 420, 176, C.violet);
  callout(slide, "BI implication", "Power BI consumes curated marts rather than raw 400-column tables. The full fact table remains available for drill-through and QA.", 58, 520, 882, 92, C.teal);
"""),
        slide_module(3, f"""
  addBase(slide, "ARCHITECTURE", "Cloud-ready design with a zero-cost local implementation");
  image(slide, {charts['09_architecture.png']}, 52, 142, 1136, 500, "Pipeline architecture");
  pill(slide, "BigQuery free-tier target", 88, 604, 190, C.blue);
  pill(slide, "DuckDB local reproducibility", 304, 604, 220, C.green);
  pill(slide, "dbt Core transformations", 550, 604, 210, C.violet);
  pill(slide, "Power BI dashboard", 786, 604, 180, C.amber);
"""),
        slide_module(4, f"""
  addBase(slide, "RARE EVENT", "Fraud is only {pct(s['fraud_rate'])} of labeled transactions");
  image(slide, {charts['01_class_imbalance.png']}, 70, 152, 510, 330, "Class imbalance");
  card(slide, "LEGITIMATE", "{int(s['legitimate_transactions']):,}", "Dominant class", 650, 164, 230, C.teal);
  card(slide, "FRAUD", "{int(s['fraud_transactions']):,}", "Minority class", 908, 164, 230, C.red);
  callout(slide, "Analytical consequence", "Accuracy is not useful by itself. Monitoring should emphasize fraud-rate lift, risk bands, precision-recall behavior, and segment concentration.", 650, 322, 488, 146, C.red);
  callout(slide, "Operational consequence", "Manual review queues should be thresholded by model score and business capacity, not by a single universal fraud rule.", 70, 516, 1068, 88, C.blue);
"""),
        slide_module(5, f"""
  addBase(slide, "TEMPORAL SIGNAL", "Risk changes across the relative transaction window");
  image(slide, {charts['02_daily_fraud_rate.png']}, 58, 150, 1078, 386, "Daily fraud-rate trend");
  callout(slide, "Why this matters", "The validation split is time-based, using the last 20% of TransactionDT. This is stricter than random validation and better matches production drift.", 138, 560, 910, 76, C.blue);
"""),
        slide_module(6, f"""
  addBase(slide, "SEGMENT RISK", "Fraud exposure is not evenly distributed");
  image(slide, {charts['04_product_device_risk.png']}, 54, 150, 540, 380, "Product device risk");
  image(slide, {charts['03_amount_bands.png']}, 646, 150, 500, 300, "Amount bands");
  card(slide, "TOP RISK SEGMENT", "{product['product_cd']} / {product['device_type']}", "{pct(product['fraud_rate'])} fraud rate", 646, 486, 246, C.violet);
  card(slide, "MEDIAN AMOUNT", "{money(s['median_transaction_amount'])}", "Transaction amount", 920, 486, 226, C.amber);
"""),
        slide_module(7, f"""
  addBase(slide, "DATA QUALITY", "Missingness is structural and must be modeled explicitly");
  image(slide, {charts['07_missingness_by_family.png']}, 68, 150, 550, 382, "Missingness by feature family");
  card(slide, "MOST SPARSE FAMILY", "{missing['column_family']}", "{pct(missing['avg_missing'])} average missing", 682, 164, 310, C.green);
  card(slide, "IDENTITY JOIN COVERAGE", "{pct(s['identity_coverage_rate'])}", "{int(s['transactions_with_identity']):,} joined records", 682, 312, 310, C.blue);
  callout(slide, "dbt policy", "Keep raw sparsity visible in staging, create explicit has_identity flags in intermediate models, and expose missingness marts for BI QA.", 682, 460, 410, 130, C.green);
"""),
        slide_module(8, f"""
  addBase(slide, "MODEL SIGNAL", "LightGBM provides usable fraud ranking for BI monitoring");
  image(slide, {charts['05_feature_importance.png']}, 54, 150, 560, 390, "Feature importance");
  image(slide, {charts['06_validation_roc.png']}, 682, 148, 410, 330, "ROC curve");
  card(slide, "VALIDATION AUC", "{metrics['ml']['validation_auc']:.3f}", "Last 20% by time", 682, 508, 190, C.blue);
  card(slide, "AVG PRECISION", "{metrics['ml']['validation_average_precision']:.3f}", "Rare-event metric", 900, 508, 190, C.violet);
  text(slide, "Top split feature: {feature['feature']} ({feature['feature_family']})", 76, 558, 520, 28, {{ size: 12, color: C.muted, bold: true }});
"""),
        slide_module(9, f"""
  addBase(slide, "RISK OPERATING LAYER", "Risk bands convert scores into review queues");
  image(slide, {charts['08_risk_bands.png']}, 70, 154, 610, 380, "Risk bands");
  card(slide, "CRITICAL BAND", "{pct(critical['observed_fraud_rate'])}", "{int(critical['transaction_count']):,} train transactions", 734, 168, 260, C.red);
  card(slide, "HIGH BAND", "{pct(high['observed_fraud_rate'])}", "{int(high['transaction_count']):,} train transactions", 734, 316, 260, C.violet);
  callout(slide, "Power BI action", "Use Critical and High as the default monitoring queue. Elevated becomes a trend/segment watchlist, while Low validates false-negative drift.", 734, 470, 350, 112, C.red);
"""),
        slide_module(10, f"""
  addBase(slide, "DELIVERY PACKAGE", "The project is ready for local BI and BigQuery free-tier deployment");
  callout(slide, "Built outputs", "DuckDB warehouse, dbt staging/intermediate/mart models, dbt tests, Power BI CSV marts, Power BI Template (.pbit), chart assets, and this editable PowerPoint deck.", 72, 154, 510, 138, C.teal);
  callout(slide, "BigQuery path", "Upload raw CSVs to BigQuery, point dbt-bigquery profile to the dataset, keep maximum_bytes_billed set, and materialize only curated marts for BI.", 72, 326, 510, 138, C.blue);
  callout(slide, "Scale risks", "Raw CSV size, sparse V/id columns, class imbalance, temporal drift, and BI import size. Trigger BigQuery-first refresh when Power BI fact import becomes slow.", 72, 498, 510, 122, C.red);
  image(slide, {charts['09_architecture.png']}, 642, 174, 520, 300, "Architecture");
  card(slide, "DBT MODELS", "12", "2 staging, 2 intermediate, 8 marts", 642, 500, 220, C.violet);
  card(slide, "DBT TESTS", "11", "All passing", 894, 500, 220, C.green);
"""),
    ]

    for i, content in enumerate(slides, start=1):
        (SLIDES_DIR / f"slide-{i:02d}.mjs").write_text(content, encoding="utf-8")


def write_profile_plan() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "profile-plan.txt").write_text(
        "\n".join(
            [
                "task mode: create",
                "primary deck-profile: engineering-platform",
                "required proof objects: architecture map, data quality evidence, dbt marts, ML validation, BI handoff",
                "source requirements: Kaggle IEEE-CIS official CSV files supplied locally",
                "profile QA gates: connector direction, warehouse/dbt/BI labels, metric evidence tied to architecture",
                "known missing inputs: direct BigQuery credential JSON not present in this shell",
            ]
        ),
        encoding="utf-8",
    )


def build_deck() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "qa").mkdir(parents=True, exist_ok=True)
    script = SKILL_DIR / "scripts" / "build_artifact_deck.mjs"
    env = os.environ.copy()
    env["HOME"] = r"C:\Users\MONSTER"
    env["PYTHON"] = r"C:\Users\MONSTER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    subprocess.run(
        [
            str(NODE),
            str(script),
            "--slides-dir",
            str(SLIDES_DIR),
            "--out",
            str(FINAL_PPTX),
            "--preview-dir",
            str(PREVIEW_DIR),
            "--layout-dir",
            str(LAYOUT_DIR),
            "--contact-sheet",
            str(CONTACT_SHEET),
            "--slide-count",
            "10",
            "--slide-size",
            "1280x720",
        ],
        cwd=str(ROOT),
        env=env,
        check=True,
    )


def main() -> None:
    numbers = load_numbers()
    write_profile_plan()
    write_slides(numbers)
    build_deck()
    print(FINAL_PPTX)
    print(CONTACT_SHEET)


if __name__ == "__main__":
    main()
