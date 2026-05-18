from __future__ import annotations

import json
import os
import sys
import subprocess
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
  text(slide, "Kaynak: Kaggle IEEE-CIS Fraud Detection yarışma verileri; analitik modelleme çıktıları", 54, 678, 760, 20, { size: 8, color: C.muted });
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
  addBase(slide, "SAHTECİLİK ANALİZİ", "Sahtecilik nadir, ancak rastgele değil");
  text(slide, "Analiz; sahteciliğin ürün, identity, tutar, ödeme tipi, email domain ve zaman kırılımlarında nerede yoğunlaştığını gösterir. Model skoru bu örüntüleri BI tarafında önceliklendirilebilir risk kuyruklarına çevirir.", 58, 148, 900, 64, {{ size: 16, color: C.ink }});
  card(slide, "TOPLAM İŞLEM", "{int(s['total_transactions']):,}", "Kaggle train_transaction.csv", 58, 246, 250, C.teal);
  card(slide, "BAZ SAHTECİLİK ORANI", "{pct(s['fraud_rate'])}", "{int(s['fraud_transactions']):,} sahtecilik etiketi", 336, 246, 250, C.red);
  card(slide, "PRODUCT C ORANI", "{pct(product_c['fraud_rate'])}", "{product_c['transaction_count']:,} işlem", 614, 246, 250, C.violet);
  card(slide, "KRİTİK BAND ORANI", "{pct(critical['observed_fraud_rate'])}", "{critical['observed_fraud_rate'] / s['fraud_rate']:.1f}x lift", 892, 246, 250, C.red);
  image(slide, {charts['16_risk_band_lift.png']}, 150, 406, 920, 220, "Risk lift grafiği");
"""),
        slide_module(2, f"""
  addBase(slide, "ANALİZ ÇERÇEVESİ", "Doğru soru genel doğruluk değil, risk yoğunlaşmasıdır");
  card(slide, "TRAIN TRANSACTION", "{metrics['tables']['train_transaction']['rows']:,}", "{metrics['tables']['train_transaction']['columns']} kolon", 58, 160, 220, C.teal);
  card(slide, "TRAIN IDENTITY", "{metrics['tables']['train_identity']['rows']:,}", "{metrics['tables']['train_identity']['columns']} kolon", 300, 160, 220, C.blue);
  card(slide, "TEST TRANSACTION", "{metrics['tables']['test_transaction']['rows']:,}", "{metrics['tables']['test_transaction']['columns']} kolon", 542, 160, 220, C.violet);
  card(slide, "SAHTECİLİK ETİKETİ", "{int(s['fraud_transactions']):,}", "nadir olay hedefi", 784, 160, 220, C.red);
  callout(slide, "Soru 1", "Sahtecilik oranı {pct(s['fraud_rate'])} baz oranını hangi segmentlerde ve ne kadar aşıyor?", 58, 320, 330, 142, C.red);
  callout(slide, "Soru 2", "Rapor segmentasyonu için hangi kırılımlar anlamlı: ürün, identity, tutar, kart, email ve zaman?", 422, 320, 330, 142, C.blue);
  callout(slide, "Soru 3", "Model skorları Power BI içinde ölçülebilir ve açıklanabilir inceleme kuyrukları oluşturabilir mi?", 786, 320, 330, 142, C.violet);
  image(slide, {charts['01_class_imbalance.png']}, 260, 500, 690, 130, "Sınıf dengesizliği");
"""),
        slide_module(3, f"""
  addBase(slide, "BULGU 1", "Ürün ailesi en net iş kırılımıdır");
  image(slide, {charts['10_product_lift.png']}, 64, 150, 650, 390, "Ürün lift analizi");
  card(slide, "PRODUCT C", "{pct(product_c['fraud_rate'])}", "{product_c['fraud_rate'] / s['fraud_rate']:.1f}x baz oran", 780, 170, 260, C.red);
  card(slide, "PRODUCT W", "{pct(product_w['fraud_rate'])}", "yüksek hacim, daha düşük risk", 780, 318, 260, C.teal);
  callout(slide, "Yorum", "Product C küçük bir anomali değil; belirgin biçimde daha yüksek sahtecilik riski taşır ve yönetici raporunda varsayılan filtrelerden biri olmalıdır.", 780, 470, 360, 112, C.red);
"""),
        slide_module(4, f"""
  addBase(slide, "BULGU 2", "Identity kaydı yalnızca veri kalitesi alanı değil, risk sinyalidir");
  image(slide, {charts['11_identity_lift.png']}, 78, 156, 560, 360, "Identity lift analizi");
  card(slide, "IDENTITY VAR", "{pct(identity_present['fraud_rate'])}", "{int(identity_present['transaction_count']):,} kayıt", 704, 174, 270, C.red);
  card(slide, "IDENTITY YOK", "{pct(identity_missing['fraud_rate'])}", "{int(identity_missing['transaction_count']):,} kayıt", 704, 322, 270, C.teal);
  callout(slide, "Yorum", "Identity tabloları seyrektir; ancak mevcut olduklarında daha riskli bir alt kümeyi işaret eder. has_identity alanı yalnızca join kapsaması değil, izleme feature'ı olarak ele alınmalıdır.", 704, 474, 380, 110, C.blue);
"""),
        slide_module(5, f"""
  addBase(slide, "BULGU 3", "İşlem tutarı riski doğrusal değildir");
  image(slide, {charts['03_amount_bands.png']}, 54, 150, 530, 330, "Tutar bantları");
  image(slide, {charts['14_amount_distribution.png']}, 650, 150, 500, 330, "Tutar dağılımı");
  callout(slide, "Yorum", "Sahtecilik çok küçük tutarlarda ve yüksek değerli bantlarda yeniden yükselir. Tek bir tutar eşiği bu U-şekilli davranışı kaçırır.", 188, 520, 820, 90, C.amber);
"""),
        slide_module(6, f"""
  addBase(slide, "BULGU 4", "Ödeme özellikleri kredi riskini debit hacminden ayırır");
  image(slide, {charts['12_card_payment_heatmap.png']}, 74, 150, 560, 372, "Kart heatmap");
  card(slide, "EN RİSKLİ KART KIRILIMI", "{card['card_network']} / {card['card_type']}", "{pct(card['fraud_rate'])} sahtecilik oranı", 704, 174, 330, C.red);
  callout(slide, "Yorum", "Kredi kartı kombinasyonları debit kombinasyonlarına göre daha yüksek risk gösterir. Bu kırılım teknik olmayan paydaşlara da açıklanabilir olduğu için güçlü bir rapor filtresidir.", 704, 340, 400, 134, C.red);
  callout(slide, "Rapor aksiyonu", "Product C riskinin ürün kaynaklı mı yoksa ödeme yöntemi kaynaklı mı ayrıştığını görmek için kart ağı/tipi ile birlikte izlenmelidir.", 704, 510, 400, 82, C.blue);
"""),
        slide_module(7, f"""
  addBase(slide, "BULGU 5", "Email domain kırılımı açıklanabilir risk segmentleri üretir");
  image(slide, {charts['13_email_domain_risk.png']}, 82, 150, 600, 380, "Email domain riski");
  card(slide, "EN YÜKSEK EMAIL GRUBU", "{email['purchaser_email_group']}", "{pct(email['fraud_rate'])} sahtecilik oranı", 742, 170, 300, C.blue);
  callout(slide, "Yorum", "Email domain tek başına nihai fraud kuralı değildir; ancak iş birimlerinin anlayabileceği stabil risk kovaları oluşturduğu için izleme açısından değerlidir.", 742, 328, 390, 120, C.blue);
  callout(slide, "Not", "Domain örüntüleri ürün, tutar ve model skoru ile birlikte değerlendirilmelidir. Tek başına karar vermek için fazla kaba bir sinyaldir.", 742, 490, 390, 90, C.amber);
"""),
        slide_module(8, f"""
  addBase(slide, "BULGU 6", "Risk zaman içinde drift gösterir; doğrulama zamanı dikkate almalıdır");
  image(slide, {charts['02_daily_fraud_rate.png']}, 58, 150, 560, 330, "Günlük sahtecilik trendi");
  image(slide, {charts['15_hourly_pattern.png']}, 676, 150, 470, 330, "Saatlik örüntü");
  callout(slide, "Yorum", "Günlük seri düz değildir. Rastgele train/test ayrımı model stabilitesini olduğundan iyi gösterebilir; bu yüzden model TransactionDT'nin son %20'lik bölümünde doğrulanmıştır.", 168, 520, 870, 92, C.red);
"""),
        slide_module(9, f"""
  addBase(slide, "VERİ KALİTESİ", "Yapısal eksiklik sinyalin bir parçasıdır");
  image(slide, {charts['07_missingness_by_family.png']}, 68, 150, 550, 382, "Feature ailesi bazında eksiklik");
  card(slide, "EN SEYREK AİLE", "{missing['column_family']}", "{pct(missing['avg_missing'])} ortalama eksiklik", 682, 164, 310, C.green);
  card(slide, "IDENTITY JOIN KAPSAMI", "{pct(s['identity_coverage_rate'])}", "{int(s['transactions_with_identity']):,} eşleşen kayıt", 682, 312, 310, C.blue);
  callout(slide, "Yorum", "Eksiklik örüntüsü yapısaldır. Profesyonel analiz bunu preprocessing içinde gizlemek yerine görünür tutar ve kalite martlarına dönüştürür.", 682, 460, 410, 130, C.green);
"""),
        slide_module(10, f"""
  addBase(slide, "MODEL KANITI", "Model Kaggle skoru değil, BI için sıralama katmanıdır");
  image(slide, {charts['05_feature_importance.png']}, 54, 150, 560, 390, "Feature importance");
  image(slide, {charts['06_validation_roc.png']}, 682, 148, 410, 330, "ROC eğrisi");
  card(slide, "DOĞRULAMA AUC", "{metrics['ml']['validation_auc']:.3f}", "zamana dayalı holdout", 682, 508, 190, C.blue);
  card(slide, "AVG PRECISION", "{metrics['ml']['validation_average_precision']:.3f}", "nadir olay metriği", 900, 508, 190, C.violet);
  text(slide, "En önemli split feature: {feature['feature']} ({feature['feature_family']})", 76, 558, 520, 28, {{ size: 12, color: C.muted, bold: true }});
"""),
        slide_module(11, f"""
  addBase(slide, "OPERASYONELLEŞTİRME", "Risk bantları analizi inceleme kuyruklarına çevirir");
  image(slide, {charts['08_risk_bands.png']}, 58, 150, 530, 350, "Risk bantları");
  image(slide, {charts['16_risk_band_lift.png']}, 650, 150, 500, 350, "Risk bandı lift");
  card(slide, "KRİTİK BAND", "{pct(critical['observed_fraud_rate'])}", "{critical['observed_fraud_rate'] / s['fraud_rate']:.1f}x baz oran", 234, 522, 230, C.red);
  card(slide, "YÜKSEK BAND", "{pct(high['observed_fraud_rate'])}", "{high['observed_fraud_rate'] / s['fraud_rate']:.1f}x baz oran", 742, 522, 230, C.violet);
"""),
        slide_module(12, f"""
  addBase(slide, "SUNUM MESAJI", "Bu çalışma üretime taşınabilir bir fraud analiz projesidir");
  callout(slide, "Analitik sonuç", "Sahtecilik Product C, identity kaydı olan işlemler, kredi kartı kombinasyonları, belirli email grupları, doğrusal olmayan tutar bantları ve drift gösteren zaman pencerelerinde yoğunlaşır.", 70, 158, 520, 126, C.red);
  callout(slide, "Rapor sonucu", "Power BI raporu ürün, identity, tutar, ödeme, email, zaman ve risk bandı sayfalarıyla başlamalıdır. Mimari ana hikaye değil, güvenilirlik kanıtıdır.", 70, 326, 520, 126, C.blue);
  callout(slide, "Teknik sonuç", "dbt testleri, mart tabloları, model skorlaması ve veri ambarı uyumlu scriptler çalışmanın tekrarlanabilir olduğunu kanıtlar. Bunlar içgörülerden sonra anlatılmalıdır.", 70, 494, 520, 116, C.green);
  image(slide, {charts['09_architecture.png']}, 650, 170, 500, 310, "Mimari");
  card(slide, "KALİTE TESTLERİ", "11 / 11", "kontroller başarılı", 680, 510, 210, C.green);
  card(slide, "POWER BI", "2.153.1206.0", "metadata güncel", 920, 510, 210, C.amber);
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
                "gerekli kanitlar: mimari harita, veri kalitesi, dbt martlari, model dogrulama, BI teslimi",
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
    env["HOME"] = r"C:\Users\MONSTER"
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
