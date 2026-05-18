from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = ROOT / "outputs" / "powerbi"
CHART_DIR = ROOT / "outputs" / "charts"
PROJECT_DIR = PBI_DIR / f"ieee_fraud_powerbi_project_{uuid.uuid4().hex[:8]}"
OUT_FILE = ROOT / "outputs" / "powerbi" / "ieee_fraud_detection_dashboard.pbit"
PBI_TOOLS = ROOT / "tools" / "pbi-tools" / "core" / "pbi-tools.core.exe"


TABLE_FILES = [
    "mart_fraud_summary.csv",
    "mart_daily_stats.csv",
    "mart_amount_bands.csv",
    "mart_product_device_stats.csv",
    "mart_email_domain_stats.csv",
    "mart_feature_missingness.csv",
    "mart_model_predictions.csv",
    "mart_risk_band_stats.csv",
    "fact_train_transactions.csv",
]


PAGES = [
    {
        "name": "Yonetici Ozeti",
        "title": "Sahtecilik nadir, ancak belirli segmentlerde yoğunlaşıyor",
        "subtitle": "Rapor önce riskin nerede kümelendiğini gösterir, teknik mimariyi destekleyici kanıt olarak konumlandırır.",
        "images": [
            ("01_class_imbalance.png", 48, 140, 360, 240),
            ("10_product_lift.png", 444, 126, 360, 250),
            ("11_identity_lift.png", 836, 126, 360, 250),
            ("16_risk_band_lift.png", 260, 420, 760, 220),
        ],
    },
    {
        "name": "Urun Identity",
        "title": "Ürün ve identity alanları en net risk ayrışmasını yaratıyor",
        "subtitle": "Product C ve identity kaydı olan işlemler baz sahtecilik oranının belirgin biçimde üzerindedir.",
        "images": [
            ("10_product_lift.png", 58, 130, 520, 360),
            ("11_identity_lift.png", 646, 130, 500, 360),
            ("04_product_device_risk.png", 260, 510, 740, 160),
        ],
    },
    {
        "name": "Odeme Email",
        "title": "Ödeme tipi ve email domain operasyonel izleme kırılımları ekliyor",
        "subtitle": "Kredi kartı kombinasyonları ve bazı purchaser email grupları daha yüksek risk göstermektedir.",
        "images": [
            ("12_card_payment_heatmap.png", 72, 130, 500, 390),
            ("13_email_domain_risk.png", 650, 130, 500, 390),
        ],
    },
    {
        "name": "Tutar Zaman",
        "title": "Tutar ve zaman örüntüleri doğrusal olmayan sahtecilik davranışı gösteriyor",
        "subtitle": "Küçük tutarlar, yüksek değerli bantlar ve göreli zaman pencereleri ayrı izlenmelidir.",
        "images": [
            ("03_amount_bands.png", 58, 132, 520, 250),
            ("14_amount_distribution.png", 650, 132, 500, 250),
            ("02_daily_fraud_rate.png", 58, 414, 560, 230),
            ("15_hourly_pattern.png", 676, 414, 470, 230),
        ],
    },
    {
        "name": "Model Riski",
        "title": "Model skorları analizi inceleme kuyruklarına dönüştürüyor",
        "subtitle": "Model nihai karar mekanizması değil, sıralama ve izleme katmanı olarak kullanılır.",
        "images": [
            ("05_feature_importance.png", 58, 130, 520, 350),
            ("06_validation_roc.png", 650, 130, 460, 350),
            ("08_risk_bands.png", 292, 506, 700, 150),
        ],
    },
    {
        "name": "Veri Kalitesi",
        "title": "Yapısal eksiklik feature engineering ihtiyacını açıklar",
        "subtitle": "Eksiklik sessizce gizlenmemeli, veri setinin izlenmesi gereken bir karakteristiği olarak ele alınmalıdır.",
        "images": [
            ("07_missingness_by_family.png", 78, 140, 520, 390),
            ("09_architecture.png", 646, 148, 500, 320),
        ],
    },
]


def ensure_clean_project() -> None:
    (PROJECT_DIR / "Model" / "tables").mkdir(parents=True)
    (PROJECT_DIR / "Model" / "cultures").mkdir(parents=True)
    (PROJECT_DIR / "Report" / "sections").mkdir(parents=True)
    (PROJECT_DIR / "StaticResources" / "RegisteredResources").mkdir(parents=True)
    (PROJECT_DIR / "StaticResources" / "SharedResources" / "BaseThemes").mkdir(parents=True)


def tmdl_name(name: str) -> str:
    safe = name.replace(".csv", "")
    return f"'{safe}'" if not safe.replace("_", "").isalnum() else safe


def dax_table(name: str) -> str:
    safe = name.replace(".csv", "")
    return f"'{safe}'"


def infer_type(series: pd.Series) -> tuple[str, str, str]:
    sample = series.dropna()
    if sample.empty:
        return "string", "type text", "none"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type", "sum"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number", "sum"
    if pd.api.types.is_bool_dtype(series):
        return "boolean", "type logical", "none"
    converted = pd.to_numeric(sample.head(1000), errors="coerce")
    if converted.notna().mean() > 0.98:
        if (converted.dropna() % 1 == 0).all():
            return "int64", "Int64.Type", "sum"
        return "double", "type number", "sum"
    return "string", "type text", "none"


def write_model() -> None:
    (PROJECT_DIR / ".pbixproj.json").write_text(
        json.dumps(
            {
                "version": "0.11",
                "created": "2026-05-18T00:00:00+03:00",
                "lastModified": "2026-05-18T00:00:00+03:00",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (PROJECT_DIR / "Version.txt").write_text("1.28", encoding="utf-8")
    (PROJECT_DIR / "ReportMetadata.json").write_text(json.dumps({"version": "5.54"}, indent=2), encoding="utf-8")
    (PROJECT_DIR / "ReportSettings.json").write_text(json.dumps({"useStylableVisualContainerHeader": True}, indent=2), encoding="utf-8")
    (PROJECT_DIR / "DiagramLayout.json").write_text(json.dumps({"version": "1.3", "diagrams": []}, indent=2), encoding="utf-8")
    (PROJECT_DIR / "Model" / "database.tmdl").write_text(
        "database 'IEEE-CIS Fraud Detection'\n\tcompatibilityLevel: 1550\n",
        encoding="utf-8",
    )
    csv_root = str(PBI_DIR.resolve()).replace("\\", "/") + "/"
    (PROJECT_DIR / "Model" / "expressions.tmdl").write_text(
        f'expression CsvRoot = "{csv_root}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\n'
        "\tannotation PBI_NavigationStepName = Navigation\n\n"
        "\tannotation PBI_ResultType = Text\n",
        encoding="utf-8",
    )
    (PROJECT_DIR / "Model" / "cultures" / "en-US.tmdl").write_text("", encoding="utf-8")

    refs = ["ref table " + tmdl_name(name) for name in TABLE_FILES]
    model = [
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        "annotation PBIDesktopVersion = 2.153.1206.0",
        "",
        'annotation PBI_QueryOrder = ["CsvRoot",' + ",".join(json.dumps(Path(name).stem) for name in TABLE_FILES) + "]",
        "",
        *refs,
        "",
    ]
    (PROJECT_DIR / "Model" / "model.tmdl").write_text("\n".join(model), encoding="utf-8")

    for file_name in TABLE_FILES:
        path = PBI_DIR / file_name
        df = pd.read_csv(path, nrows=5000)
        table_name = Path(file_name).stem
        lines = [f"table {tmdl_name(file_name)}", ""]
        for col in df.columns:
            dtype, _m_type, summarize = infer_type(df[col])
            col_name = f"'{col}'" if not col.replace("_", "").isalnum() else col
            lines += [
                f"\tcolumn {col_name}",
                f"\t\tdataType: {dtype}",
            ]
            if dtype == "int64":
                lines.append("\t\tformatString: 0")
            elif dtype == "double":
                lines.append('\t\tformatString: 0.00')
            lines += [
                f"\t\tsummarizeBy: {summarize}",
                f"\t\tsourceColumn: {col_name}",
                "",
                "\t\tannotation SummarizationSetBy = Automatic",
                "",
            ]

        if table_name == "fact_train_transactions":
            lines += [
                "\tmeasure Transactions = COUNTROWS('fact_train_transactions')",
                '\t\tformatString: #,0',
                "",
                "\tmeasure 'Fraud Transactions' = SUM('fact_train_transactions'[is_fraud])",
                '\t\tformatString: #,0',
                "",
                "\tmeasure 'Fraud Rate' = DIVIDE([Fraud Transactions], [Transactions])",
                '\t\tformatString: 0.00%',
                "",
                "\tmeasure 'Average Amount' = AVERAGE('fact_train_transactions'[transaction_amount])",
                '\t\tformatString: "$"#,0.00',
                "",
                "\tmeasure 'Predicted Risk' = AVERAGE('fact_train_transactions'[predicted_fraud_probability])",
                '\t\tformatString: 0.00%',
                "",
            ]

        transforms = []
        for col in df.columns:
            _dtype, m_type, _summarize = infer_type(df[col])
            transforms.append(f'{{"{col}", {m_type}}}')
        transform_expr = ", ".join(transforms)
        lines += [
            f"\tpartition {tmdl_name(file_name)} = m",
            "\t\tmode: import",
            "\t\tsource =",
            "\t\t\t\tlet",
            f'\t\t\t\t    Source = Csv.Document(File.Contents(CsvRoot & "{file_name}"),[Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            f'\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{transform_expr}}})',
            "\t\t\t\tin",
            '\t\t\t\t    #"Changed Type"',
            "",
            "\tannotation PBI_ResultType = Table",
            "",
        ]
        (PROJECT_DIR / "Model" / "tables" / f"{table_name}.tmdl").write_text("\n".join(lines), encoding="utf-8")


def text_config(name: str, text: str, x: float, y: float, width: float, height: float, font_size: int = 18, bold: bool = False) -> dict:
    return {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 1000, "width": width, "height": height}}],
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontSize": f"{font_size}pt",
                                                "fontWeight": "bold" if bold else "normal",
                                                "color": "#17212B",
                                            },
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
        },
    }


def image_config(name: str, item_name: str, x: float, y: float, width: float, height: float, z: int) -> dict:
    return {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height}}],
        "singleVisual": {
            "visualType": "image",
            "drillFilterOtherVisuals": True,
            "objects": {
                "general": [
                    {
                        "properties": {
                            "imageUrl": {
                                "expr": {
                                    "ResourcePackageItem": {
                                        "PackageName": "RegisteredResources",
                                        "PackageType": 1,
                                        "ItemName": item_name,
                                    }
                                }
                            }
                        }
                    }
                ]
            },
        },
    }


def write_visual(container_dir: Path, config: dict, x: float, y: float, width: float, height: float, z: int) -> None:
    container_dir.mkdir(parents=True)
    (container_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (container_dir / "filters.json").write_text("[]", encoding="utf-8")
    (container_dir / "visualContainer.json").write_text(
        json.dumps({"x": x, "y": y, "z": z, "width": width, "height": height}, indent=2),
        encoding="utf-8",
    )


def write_report() -> None:
    resources = []
    for chart in sorted(CHART_DIR.glob("*.png")):
        target = PROJECT_DIR / "StaticResources" / "RegisteredResources" / chart.name
        shutil.copy2(chart, target)
        resources.append({"name": chart.name, "path": chart.name, "type": 100})

    (PROJECT_DIR / "StaticResources" / "SharedResources" / "BaseThemes" / "CY19SU12.json").write_text(
        json.dumps({"name": "IEEE Fraud Theme", "dataColors": ["#0F766E", "#2563EB", "#B42318", "#B7791F", "#6D28D9"]}, indent=2),
        encoding="utf-8",
    )
    report_json = {
        "id": 0,
        "layoutOptimization": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "disabled": False,
                    "items": [{"name": "CY19SU12", "path": "BaseThemes/CY19SU12.json", "type": 202}],
                    "name": "SharedResources",
                    "type": 2,
                }
            },
            {"resourcePackage": {"disabled": False, "items": resources, "name": "RegisteredResources", "type": 1}},
        ],
    }
    (PROJECT_DIR / "Report" / "report.json").write_text(json.dumps(report_json, indent=2), encoding="utf-8")
    (PROJECT_DIR / "Report" / "config.json").write_text("{}", encoding="utf-8")

    for index, page in enumerate(PAGES):
        section_id = f"{index:03d}_{page['name'].replace(' ', '_')}"
        section = PROJECT_DIR / "Report" / "sections" / section_id
        visual_root = section / "visualContainers"
        visual_root.mkdir(parents=True)
        (section / "section.json").write_text(
            json.dumps({"displayName": page["name"], "displayOption": 1, "height": 720, "name": f"ReportSection{index}", "ordinal": index, "width": 1280}, indent=2),
            encoding="utf-8",
        )
        (section / "config.json").write_text("{}", encoding="utf-8")
        (section / "filters.json").write_text("[]", encoding="utf-8")

        write_visual(
            visual_root / "00000_textbox_title",
            text_config(f"title_{index}", page["title"], 44, 28, 1100, 48, 22, True),
            44,
            28,
            1100,
            48,
            1000,
        )
        write_visual(
            visual_root / "00001_textbox_subtitle",
            text_config(f"subtitle_{index}", page["subtitle"], 46, 76, 1050, 42, 12, False),
            46,
            76,
            1050,
            42,
            1001,
        )
        for visual_index, (image_name, x, y, w, h) in enumerate(page["images"], start=2):
            write_visual(
                visual_root / f"{visual_index:05d}_image_{Path(image_name).stem}",
                image_config(f"image_{index}_{visual_index}", image_name, x, y, w, h, visual_index),
                x,
                y,
                w,
                h,
                visual_index,
            )


def compile_template() -> None:
    if not PBI_TOOLS.exists():
        raise FileNotFoundError(f"pbi-tools Core not found: {PBI_TOOLS}")
    if OUT_FILE.exists():
        OUT_FILE.unlink()
    subprocess.run(
        [str(PBI_TOOLS), "compile", str(PROJECT_DIR), str(OUT_FILE), "PBIT", "true"],
        check=True,
        cwd=str(ROOT),
    )


def main() -> None:
    ensure_clean_project()
    write_model()
    write_report()
    compile_template()
    (PBI_DIR / "POWERBI_OPEN_NOTES.md").write_text(
        "# Power BI Açılış Notları\n\n"
        "Rapor Power BI Desktop `2.153.1206.0` sürümüyle uyumlu olacak şekilde hazırlanmıştır.\n\n"
        "`ieee_fraud_detection_dashboard.pbit` dosyasını açın. `CsvRoot` parametresi sorulursa proje aynı klasörde kaldığı sürece varsayılan yolu koruyun. "
        "Template başka bir konuma taşındıysa `CsvRoot` değerini CSV martlarının bulunduğu klasöre yönlendirin.\n\n"
        "Power BI Desktop template uyumluluğu uyarısı verirse CSV dosyalarını manuel içe aktarın ve sayfa/ölçü düzeni için `powerbi_dashboard_spec.md` dosyasını kullanın. "
        "Temel veri modeli dbt ile üretilen CSV mart katmanıdır.",
        encoding="utf-8",
    )
    print(OUT_FILE)


if __name__ == "__main__":
    main()
