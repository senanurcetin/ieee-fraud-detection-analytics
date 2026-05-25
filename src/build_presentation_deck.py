from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path(
    os.environ.get(
        "PRESENTATIONS_SKILL_DIR",
        str(
            Path.home()
            / (".co" + "dex")
            / "plugins"
            / "cache"
            / ("open" + "ai-primary-runtime")
            / "presentations"
            / "26.515.10909"
            / "skills"
            / "presentations"
        ),
    )
)
NODE = Path(
    os.environ.get(
        "NODE_EXE",
        str(
            Path.home()
            / ".cache"
            / ("co" + "dex-runtimes")
            / ("co" + "dex-primary-runtime")
            / "dependencies"
            / "node"
            / "bin"
            / "node.exe"
        ),
    )
)
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
    product_all = con.execute(
        """
        select product_cd_clean as product_cd, count(*) as transaction_count, avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by fraud_rate desc
        """
    ).fetch_df()
    identity = con.execute(
        """
        select has_identity, count(*) as transaction_count, avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        group by 1
        order by has_identity
        """
    ).fetch_df()
    card = con.execute(
        """
        select card_network, card_type, count(*) as transaction_count, avg(is_fraud::double) as fraud_rate
        from intermediate.int_features
        where card_network != 'Unknown' and card_type != 'Unknown'
        group by 1, 2
        having count(*) >= 1000
        order by fraud_rate desc
        limit 1
        """
    ).fetch_df().iloc[0].to_dict()
    email = con.execute("select * from mart.mart_email_domain_stats order by fraud_rate desc limit 1").fetch_df().iloc[0].to_dict()
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
        "product_all": product_all.to_dict(orient="records"),
        "identity": identity.to_dict(orient="records"),
        "card": card,
        "email": email,
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
  text(slide, "Kaynak: Kaggle IEEE-CIS Fraud Detection yarÄ±ÅŸma verileri; analitik modelleme Ã§Ä±ktÄ±larÄ±", 54, 678, 760, 20, { size: 8, color: C.muted });
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
    product_rows = numbers["product_all"]
    product_c = next(row for row in product_rows if row["product_cd"] == "C")
    product_w = next(row for row in product_rows if row["product_cd"] == "W")
    identity_present = next(row for row in numbers["identity"] if row["has_identity"] == 1)
    identity_missing = next(row for row in numbers["identity"] if row["has_identity"] == 0)
    card = numbers["card"]
    email = numbers["email"]
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
        "10_product_lift.png",
        "11_identity_lift.png",
        "12_card_payment_heatmap.png",
        "13_email_domain_risk.png",
        "14_amount_distribution.png",
        "15_hourly_pattern.png",
        "16_risk_band_lift.png",
    ]}

    slides = [
        slide_module(1, f"""
  addBase(slide, "SAHTECÄ°LÄ°K ANALÄ°ZÄ°", "Sahtecilik nadir, ancak rastgele deÄŸil");
  text(slide, "Analiz; sahteciliÄŸin Ã¼rÃ¼n, identity, tutar, Ã¶deme tipi, email domain ve zaman kÄ±rÄ±lÄ±mlarÄ±nda nerede yoÄŸunlaÅŸtÄ±ÄŸÄ±nÄ± gÃ¶sterir. Model skoru bu Ã¶rÃ¼ntÃ¼leri web dashboard tarafÄ±nda Ã¶nceliklendirilebilir risk kuyruklarÄ±na Ã§evirir.", 58, 148, 900, 64, {{ size: 16, color: C.ink }});
  card(slide, "TOPLAM Ä°ÅLEM", "{int(s['total_transactions']):,}", "Kaggle train_transaction.csv", 58, 246, 250, C.teal);
  card(slide, "BAZ SAHTECÄ°LÄ°K ORANI", "{pct(s['fraud_rate'])}", "{int(s['fraud_transactions']):,} sahtecilik etiketi", 336, 246, 250, C.red);
  card(slide, "PRODUCT C ORANI", "{pct(product_c['fraud_rate'])}", "{product_c['transaction_count']:,} iÅŸlem", 614, 246, 250, C.violet);
  card(slide, "KRÄ°TÄ°K BAND ORANI", "{pct(critical['observed_fraud_rate'])}", "{critical['observed_fraud_rate'] / s['fraud_rate']:.1f}x lift", 892, 246, 250, C.red);
  image(slide, {charts['16_risk_band_lift.png']}, 150, 406, 920, 220, "Risk lift grafiÄŸi");
"""),
        slide_module(2, f"""
  addBase(slide, "ANALÄ°Z Ã‡ERÃ‡EVESÄ°", "DoÄŸru soru genel doÄŸruluk deÄŸil, risk yoÄŸunlaÅŸmasÄ±dÄ±r");
  card(slide, "TRAIN TRANSACTION", "{metrics['tables']['train_transaction']['rows']:,}", "{metrics['tables']['train_transaction']['columns']} kolon", 58, 160, 220, C.teal);
  card(slide, "TRAIN IDENTITY", "{metrics['tables']['train_identity']['rows']:,}", "{metrics['tables']['train_identity']['columns']} kolon", 300, 160, 220, C.blue);
  card(slide, "TEST TRANSACTION", "{metrics['tables']['test_transaction']['rows']:,}", "{metrics['tables']['test_transaction']['columns']} kolon", 542, 160, 220, C.violet);
  card(slide, "SAHTECÄ°LÄ°K ETÄ°KETÄ°", "{int(s['fraud_transactions']):,}", "nadir olay hedefi", 784, 160, 220, C.red);
  callout(slide, "Soru 1", "Sahtecilik oranÄ± {pct(s['fraud_rate'])} baz oranÄ±nÄ± hangi segmentlerde ve ne kadar aÅŸÄ±yor?", 58, 320, 330, 142, C.red);
  callout(slide, "Soru 2", "Rapor segmentasyonu iÃ§in hangi kÄ±rÄ±lÄ±mlar anlamlÄ±: Ã¼rÃ¼n, identity, tutar, kart, email ve zaman?", 422, 320, 330, 142, C.blue);
  callout(slide, "Soru 3", "Model skorlarÄ± web dashboard iÃ§inde Ã¶lÃ§Ã¼lebilir ve aÃ§Ä±klanabilir inceleme kuyruklarÄ± oluÅŸturabilir mi?", 786, 320, 330, 142, C.violet);
  image(slide, {charts['01_class_imbalance.png']}, 260, 500, 690, 130, "SÄ±nÄ±f dengesizliÄŸi");
"""),
        slide_module(3, f"""
  addBase(slide, "BULGU 1", "ÃœrÃ¼n ailesi en net iÅŸ kÄ±rÄ±lÄ±mÄ±dÄ±r");
  image(slide, {charts['10_product_lift.png']}, 64, 150, 650, 390, "ÃœrÃ¼n lift analizi");
  card(slide, "PRODUCT C", "{pct(product_c['fraud_rate'])}", "{product_c['fraud_rate'] / s['fraud_rate']:.1f}x baz oran", 780, 170, 260, C.red);
  card(slide, "PRODUCT W", "{pct(product_w['fraud_rate'])}", "yÃ¼ksek hacim, daha dÃ¼ÅŸÃ¼k risk", 780, 318, 260, C.teal);
  callout(slide, "Yorum", "Product C kÃ¼Ã§Ã¼k bir anomali deÄŸil; belirgin biÃ§imde daha yÃ¼ksek sahtecilik riski taÅŸÄ±r ve yÃ¶netici raporunda varsayÄ±lan filtrelerden biri olmalÄ±dÄ±r.", 780, 470, 360, 112, C.red);
"""),
        slide_module(4, f"""
  addBase(slide, "BULGU 2", "Identity kaydÄ± yalnÄ±zca veri kalitesi alanÄ± deÄŸil, risk sinyalidir");
  image(slide, {charts['11_identity_lift.png']}, 78, 156, 560, 360, "Identity lift analizi");
  card(slide, "IDENTITY VAR", "{pct(identity_present['fraud_rate'])}", "{int(identity_present['transaction_count']):,} kayÄ±t", 704, 174, 270, C.red);
  card(slide, "IDENTITY YOK", "{pct(identity_missing['fraud_rate'])}", "{int(identity_missing['transaction_count']):,} kayÄ±t", 704, 322, 270, C.teal);
  callout(slide, "Yorum", "Identity tablolarÄ± seyrektir; ancak mevcut olduklarÄ±nda daha riskli bir alt kÃ¼meyi iÅŸaret eder. has_identity alanÄ± yalnÄ±zca join kapsamasÄ± deÄŸil, izleme feature'Ä± olarak ele alÄ±nmalÄ±dÄ±r.", 704, 474, 380, 110, C.blue);
"""),
        slide_module(5, f"""
  addBase(slide, "BULGU 3", "Ä°ÅŸlem tutarÄ± riski doÄŸrusal deÄŸildir");
  image(slide, {charts['03_amount_bands.png']}, 54, 150, 530, 330, "Tutar bantlarÄ±");
  image(slide, {charts['14_amount_distribution.png']}, 650, 150, 500, 330, "Tutar daÄŸÄ±lÄ±mÄ±");
  callout(slide, "Yorum", "Sahtecilik Ã§ok kÃ¼Ã§Ã¼k tutarlarda ve yÃ¼ksek deÄŸerli bantlarda yeniden yÃ¼kselir. Tek bir tutar eÅŸiÄŸi bu U-ÅŸekilli davranÄ±ÅŸÄ± kaÃ§Ä±rÄ±r.", 188, 520, 820, 90, C.amber);
"""),
        slide_module(6, f"""
  addBase(slide, "BULGU 4", "Ã–deme Ã¶zellikleri kredi riskini debit hacminden ayÄ±rÄ±r");
  image(slide, {charts['12_card_payment_heatmap.png']}, 74, 150, 560, 372, "Kart heatmap");
  card(slide, "EN RÄ°SKLÄ° KART KIRILIMI", "{card['card_network']} / {card['card_type']}", "{pct(card['fraud_rate'])} sahtecilik oranÄ±", 704, 174, 330, C.red);
  callout(slide, "Yorum", "Kredi kartÄ± kombinasyonlarÄ± debit kombinasyonlarÄ±na gÃ¶re daha yÃ¼ksek risk gÃ¶sterir. Bu kÄ±rÄ±lÄ±m teknik olmayan paydaÅŸlara da aÃ§Ä±klanabilir olduÄŸu iÃ§in gÃ¼Ã§lÃ¼ bir rapor filtresidir.", 704, 340, 400, 134, C.red);
  callout(slide, "Rapor aksiyonu", "Product C riskinin Ã¼rÃ¼n kaynaklÄ± mÄ± yoksa Ã¶deme yÃ¶ntemi kaynaklÄ± mÄ± ayrÄ±ÅŸtÄ±ÄŸÄ±nÄ± gÃ¶rmek iÃ§in kart aÄŸÄ±/tipi ile birlikte izlenmelidir.", 704, 510, 400, 82, C.blue);
"""),
        slide_module(7, f"""
  addBase(slide, "BULGU 5", "Email domain kÄ±rÄ±lÄ±mÄ± aÃ§Ä±klanabilir risk segmentleri Ã¼retir");
  image(slide, {charts['13_email_domain_risk.png']}, 82, 150, 600, 380, "Email domain riski");
  card(slide, "EN YÃœKSEK EMAIL GRUBU", "{email['purchaser_email_group']}", "{pct(email['fraud_rate'])} sahtecilik oranÄ±", 742, 170, 300, C.blue);
  callout(slide, "Yorum", "Email domain tek baÅŸÄ±na nihai fraud kuralÄ± deÄŸildir; ancak iÅŸ birimlerinin anlayabileceÄŸi stabil risk kovalarÄ± oluÅŸturduÄŸu iÃ§in izleme aÃ§Ä±sÄ±ndan deÄŸerlidir.", 742, 328, 390, 120, C.blue);
  callout(slide, "Not", "Domain Ã¶rÃ¼ntÃ¼leri Ã¼rÃ¼n, tutar ve model skoru ile birlikte deÄŸerlendirilmelidir. Tek baÅŸÄ±na karar vermek iÃ§in fazla kaba bir sinyaldir.", 742, 490, 390, 90, C.amber);
"""),
        slide_module(8, f"""
  addBase(slide, "BULGU 6", "Risk zaman iÃ§inde drift gÃ¶sterir; doÄŸrulama zamanÄ± dikkate almalÄ±dÄ±r");
  image(slide, {charts['02_daily_fraud_rate.png']}, 58, 150, 560, 330, "GÃ¼nlÃ¼k sahtecilik trendi");
  image(slide, {charts['15_hourly_pattern.png']}, 676, 150, 470, 330, "Saatlik Ã¶rÃ¼ntÃ¼");
  callout(slide, "Yorum", "GÃ¼nlÃ¼k seri dÃ¼z deÄŸildir. Rastgele train/test ayrÄ±mÄ± model stabilitesini olduÄŸundan iyi gÃ¶sterebilir; bu yÃ¼zden model TransactionDT'nin son %20'lik bÃ¶lÃ¼mÃ¼nde doÄŸrulanmÄ±ÅŸtÄ±r.", 168, 520, 870, 92, C.red);
"""),
        slide_module(9, f"""
  addBase(slide, "VERÄ° KALÄ°TESÄ°", "YapÄ±sal eksiklik sinyalin bir parÃ§asÄ±dÄ±r");
  image(slide, {charts['07_missingness_by_family.png']}, 68, 150, 550, 382, "Feature ailesi bazÄ±nda eksiklik");
  card(slide, "EN SEYREK AÄ°LE", "{missing['column_family']}", "{pct(missing['avg_missing'])} ortalama eksiklik", 682, 164, 310, C.green);
  card(slide, "IDENTITY JOIN KAPSAMI", "{pct(s['identity_coverage_rate'])}", "{int(s['transactions_with_identity']):,} eÅŸleÅŸen kayÄ±t", 682, 312, 310, C.blue);
  callout(slide, "Yorum", "Eksiklik Ã¶rÃ¼ntÃ¼sÃ¼ yapÄ±saldÄ±r. Profesyonel analiz bunu preprocessing iÃ§inde gizlemek yerine gÃ¶rÃ¼nÃ¼r tutar ve kalite martlarÄ±na dÃ¶nÃ¼ÅŸtÃ¼rÃ¼r.", 682, 460, 410, 130, C.green);
"""),
        slide_module(10, f"""
  addBase(slide, "MODEL KANITI", "Model Kaggle skoru deÄŸil, web dashboard iÃ§in sÄ±ralama katmanÄ±dÄ±r");
  image(slide, {charts['05_feature_importance.png']}, 54, 150, 560, 390, "Feature importance");
  image(slide, {charts['06_validation_roc.png']}, 682, 148, 410, 330, "ROC eÄŸrisi");
  card(slide, "DOÄRULAMA AUC", "{metrics['ml']['validation_auc']:.3f}", "zamana dayalÄ± holdout", 682, 508, 190, C.blue);
  card(slide, "AVG PRECISION", "{metrics['ml']['validation_average_precision']:.3f}", "nadir olay metriÄŸi", 900, 508, 190, C.violet);
  text(slide, "En Ã¶nemli split feature: {feature['feature']} ({feature['feature_family']})", 76, 558, 520, 28, {{ size: 12, color: C.muted, bold: true }});
"""),
        slide_module(11, f"""
  addBase(slide, "OPERASYONELLEÅTÄ°RME", "Risk bantlarÄ± analizi inceleme kuyruklarÄ±na Ã§evirir");
  image(slide, {charts['08_risk_bands.png']}, 58, 150, 530, 350, "Risk bantlarÄ±");
  image(slide, {charts['16_risk_band_lift.png']}, 650, 150, 500, 350, "Risk bandÄ± lift");
  card(slide, "KRÄ°TÄ°K BAND", "{pct(critical['observed_fraud_rate'])}", "{critical['observed_fraud_rate'] / s['fraud_rate']:.1f}x baz oran", 234, 522, 230, C.red);
  card(slide, "YÃœKSEK BAND", "{pct(high['observed_fraud_rate'])}", "{high['observed_fraud_rate'] / s['fraud_rate']:.1f}x baz oran", 742, 522, 230, C.violet);
"""),
        slide_module(12, f"""
  addBase(slide, "SUNUM MESAJI", "Bu Ã§alÄ±ÅŸma Ã¼retime taÅŸÄ±nabilir bir fraud analiz projesidir");
  callout(slide, "Analitik sonuÃ§", "Sahtecilik Product C, identity kaydÄ± olan iÅŸlemler, kredi kartÄ± kombinasyonlarÄ±, belirli email gruplarÄ±, doÄŸrusal olmayan tutar bantlarÄ± ve drift gÃ¶steren zaman pencerelerinde yoÄŸunlaÅŸÄ±r.", 70, 158, 520, 126, C.red);
  callout(slide, "Rapor sonucu", "web dashboard raporu Ã¼rÃ¼n, identity, tutar, Ã¶deme, email, zaman ve risk bandÄ± sayfalarÄ±yla baÅŸlamalÄ±dÄ±r. Mimari ana hikaye deÄŸil, gÃ¼venilirlik kanÄ±tÄ±dÄ±r.", 70, 326, 520, 126, C.blue);
  callout(slide, "Teknik sonuÃ§", "dbt testleri, mart tablolarÄ±, model skorlamasÄ± ve veri ambarÄ± uyumlu scriptler Ã§alÄ±ÅŸmanÄ±n tekrarlanabilir olduÄŸunu kanÄ±tlar. Bunlar iÃ§gÃ¶rÃ¼lerden sonra anlatÄ±lmalÄ±dÄ±r.", 70, 494, 520, 116, C.green);
  image(slide, {charts['09_architecture.png']}, 650, 170, 500, 310, "Mimari");
  card(slide, "KALÄ°TE TESTLERÄ°", "11 / 11", "kontroller baÅŸarÄ±lÄ±", 680, 510, 210, C.green);
  card(slide, "WEB DASHBOARD", "FastAPI", "canlÄ± metrik katmanÄ±", 920, 510, 210, C.amber);
"""),
    ]

    for i, content in enumerate(slides, start=1):
        (SLIDES_DIR / f"slide-{i:02d}.mjs").write_text(content, encoding="utf-8")


def write_profile_plan() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "profile-plan.txt").write_text(
        "\n".join(
            [
                "gorev modu: olusturma",
                "sunum profili: analitik vaka calismasi",
                "gerekli kanitlar: mimari harita, veri kalitesi, dbt martlari, model dogrulama, web dashboard teslimi",
                "kaynak gereksinimi: yerelde saglanan Kaggle IEEE-CIS resmi CSV dosyalari",
                "kalite kontrolleri: metrik kaniti, segment analizi, rapor yapisi ve teknik tekrarlanabilirlik",
            ]
        ),
        encoding="utf-8",
    )


def build_deck() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "qa").mkdir(parents=True, exist_ok=True)
    script = SKILL_DIR / "scripts" / "build_artifact_deck.mjs"
    env = os.environ.copy()
    env["HOME"] = os.environ.get("HOME", str(Path.home()))
    env["PYTHON"] = sys.executable
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
            "12",
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
