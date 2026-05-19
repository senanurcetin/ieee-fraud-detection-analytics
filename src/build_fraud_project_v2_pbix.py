from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE_PBIX = ROOT / "outputs" / "powerbi" / "fraud_project_v2.pbix"
LAYOUT_TEMPLATE = ROOT / "outputs" / "powerbi" / "fraud_project_dashboard.pbit"
POWERBI_DIR = ROOT / "powerbi"
FINAL_PBIX = POWERBI_DIR / "fraud_project_v2.pbix"

PAGE_ORDER = [
    ("Yonetici Ozeti", "Yönetici Özeti"),
    ("Urun Identity", "Risk Konsantrasyonu"),
    ("Tutar Zaman", "Tutar ve Zaman Analizi"),
    ("Odeme Email", "Ödeme ve Email Segmentleri"),
    ("Model Riski", "Model Skorlama ve Risk Bantları"),
    ("Veri Kalitesi", "Veri Kalitesi ve Mimari"),
]

PAGE_COPY = {
    "Yönetici Özeti": (
        "Sahtecilik nadir, ancak belirli segmentlerde yoğunlaşıyor",
        "Yönetim odağı genel hacimden çok riskin kümelendiği ürün, tutar ve risk bandı kesitlerine çevrilmelidir.",
    ),
    "Risk Konsantrasyonu": (
        "Ürün ve cihaz kırılımları risk ayrışmasını netleştiriyor",
        "Product C, mobil işlem davranışı ve yüksek risk bandı birlikte izlendiğinde operasyon kuyruğu daha hedefli yönetilir.",
    ),
    "Tutar ve Zaman Analizi": (
        "Tutar ve işlem saati örüntüleri doğrusal olmayan davranış gösteriyor",
        "Düşük tutar, yüksek tutar ve gün içi pencereler ayrı izlenmediğinde segment riski ortalamada kaybolur.",
    ),
    "Ödeme ve Email Segmentleri": (
        "Ödeme tipi ve email domain operasyonel izleme kırılımları ekliyor",
        "Kart ağı, kart tipi ve purchaser email grubu fraud riskini iş birimleri için okunabilir segmentlere dönüştürür.",
    ),
    "Model Skorlama ve Risk Bantları": (
        "Model skorları karar değil, inceleme önceliği üretir",
        "Risk bantları fraud inceleme kapasitesini yüksek olasılıklı işlem gruplarına yönlendiren bir sıralama katmanıdır.",
    ),
    "Veri Kalitesi ve Mimari": (
        "Veri kalitesi ölçülür ve mimari akış rapor güvenini destekler",
        "Eksiklik yapısal bir veri karakteristiği olarak izlenir; dbt ve BigQuery kontrolleri rapor katmanını doğrular.",
    ),
}


def read_layout_template() -> dict:
    if not LAYOUT_TEMPLATE.exists():
        raise FileNotFoundError(f"Layout template not found: {LAYOUT_TEMPLATE}")
    with ZipFile(LAYOUT_TEMPLATE, "r") as zf:
        return json.loads(zf.read("Report/Layout").decode("utf-16le"))


def normalize_layout(layout: dict) -> dict:
    source_sections = {section["displayName"]: section for section in layout["sections"]}
    sections = []
    for ordinal, (old_name, new_name) in enumerate(PAGE_ORDER):
        section = source_sections[old_name]
        section["displayName"] = new_name
        section["ordinal"] = ordinal
        section["name"] = f"ReportSection{ordinal}"
        section["width"] = 1280
        section["height"] = 720
        section["visualContainers"] = []
        sections.append(section)

    layout["sections"] = sections
    layout["resourcePackages"] = [
        package
        for package in layout.get("resourcePackages", [])
        if package.get("resourcePackage", {}).get("name") != "RegisteredResources"
    ]
    layout["config"] = json.dumps(
        {
            "version": "5.72",
            "themeCollection": {"baseTheme": {"name": "CY26SU04", "type": 2}},
            "activeSectionIndex": 0,
            "defaultDrillFilterOtherVisuals": True,
            "settings": {
                "useNewFilterPaneExperience": True,
                "allowChangeFilterTypes": True,
                "useStylableVisualContainerHeader": True,
                "useEnhancedTooltips": True,
                "exportDataMode": 1,
            },
        },
        separators=(",", ":"),
    )
    return layout


def textbox_visual(
    name: str,
    text: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    font_size: int = 14,
    bold: bool = False,
    color: str = "#17212B",
) -> dict:
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height}}],
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
                                                "color": color,
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
    return {
        "x": x,
        "y": y,
        "z": z,
        "width": width,
        "height": height,
        "config": json.dumps(config, ensure_ascii=False, separators=(",", ":")),
        "filters": "[]",
    }


def source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}


def column_expr(alias: str, column: str) -> dict:
    return {"Column": {"Expression": source_ref(alias), "Property": column}}


def column_select(alias: str, table: str, column: str) -> dict:
    return {
        "Column": {"Expression": source_ref(alias), "Property": column},
        "Name": f"{table}.{column}",
    }


def sum_select(alias: str, table: str, column: str) -> dict:
    return {
        "Aggregation": {
            "Expression": {"Column": {"Expression": source_ref(alias), "Property": column}},
            "Function": 0,
        },
        "Name": f"Sum({table}.{column})",
    }


def query_from_selects(table: str, alias: str, selects: list[dict], order_by: str | None = None) -> dict:
    query = {
        "Version": 2,
        "From": [{"Name": alias, "Entity": table, "Type": 0}],
        "Select": selects,
    }
    if order_by:
        query["OrderBy"] = [{"Direction": 1, "Expression": column_expr(alias, order_by)}]
    return query


def semantic_query_payload(query: dict, projection_count: int, window_count: int = 500) -> str:
    payload = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": query,
                    "Binding": {
                        "Primary": {"Groupings": [{"Projections": list(range(projection_count))}]},
                        "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": window_count}}},
                        "Version": 1,
                    },
                    "ExecutionMetricsKind": 1,
                }
            }
        ]
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def format_for(value_type: str) -> str | None:
    if value_type == "percent":
        return "0.0%"
    if value_type == "whole":
        return "#,0"
    if value_type == "decimal":
        return "#,0.0"
    return None


def data_transforms(selects: list[tuple[str, str, str, str]], projection_ordering: dict[str, list[int]]) -> str:
    metadata = []
    select_payload = []
    for display_name, query_name, role, value_type in selects:
        type_code = 2048 if value_type == "category" else 259
        metadata_item = {"Restatement": display_name, "Name": query_name, "Type": type_code}
        select_item = {
            "displayName": display_name,
            "queryName": query_name,
            "roles": {role: True},
            "type": {"category": None} if value_type == "category" else {"numeric": True},
        }
        format_string = format_for(value_type)
        if format_string:
            metadata_item["Format"] = format_string
            select_item["format"] = format_string
        metadata.append(metadata_item)
        select_payload.append(select_item)

    payload = {
        "selects": select_payload,
        "projectionOrdering": projection_ordering,
        "queryMetadata": {"Select": metadata},
        "visualElements": [],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def visual_objects(visual_type: str, color: str, show_title: bool) -> dict:
    title = {
        "show": {"expr": {"Literal": {"Value": "true" if show_title else "false"}}},
        "fontColor": {"solid": {"color": "#17212B"}},
        "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
    }
    objects = {
        "title": [{"properties": title}],
        "labels": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "labelDisplayUnits": {"expr": {"Literal": {"Value": "0D"}}},
                    "labelPrecision": {"expr": {"Literal": {"Value": "1D"}}},
                    "color": {"solid": {"color": "#17212B"}},
                }
            }
        ],
        "dataPoint": [{"properties": {"defaultColor": {"solid": {"color": color}}}}],
    }
    if visual_type == "card":
        objects.update(
            {
                "categoryLabels": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "calloutValue": [
                    {
                        "properties": {
                            "labelDisplayUnits": {"expr": {"Literal": {"Value": "0D"}}},
                            "fontColor": {"solid": {"color": "#17212B"}},
                        }
                    }
                ],
            }
        )
    elif visual_type in {"clusteredColumnChart", "clusteredBarChart"}:
        objects.update(
            {
                "categoryAxis": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                            "fontColor": {"solid": {"color": "#5E6872"}},
                        }
                    }
                ],
                "valueAxis": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                            "labelDisplayUnits": {"expr": {"Literal": {"Value": "0D"}}},
                            "fontColor": {"solid": {"color": "#5E6872"}},
                        }
                    }
                ],
            }
        )
    return objects


def native_visual(
    name: str,
    visual_type: str,
    table: str,
    alias: str,
    projections: dict[str, list[str]],
    selects: list[dict],
    transform_selects: list[tuple[str, str, str, str]],
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    order_by: str | None = None,
    color: str = "#1B7F79",
    show_title: bool = False,
) -> dict:
    query = query_from_selects(table, alias, selects, order_by)
    config = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height}}],
        "singleVisual": {
            "visualType": visual_type,
            "projections": {
                role: [{"queryRef": query_ref} for query_ref in query_refs]
                for role, query_refs in projections.items()
            },
            "prototypeQuery": query,
            "drillFilterOtherVisuals": True,
            "objects": visual_objects(visual_type, color, show_title),
        },
    }
    projection_ordering = {
        role: [
            next(
                index
                for index, (_display, query_ref, transform_role, _value_type) in enumerate(transform_selects)
                if query_ref == query_name and transform_role == role
            )
            for query_name in query_refs
        ]
        for role, query_refs in projections.items()
    }
    return {
        "x": x,
        "y": y,
        "z": z,
        "width": width,
        "height": height,
        "config": json.dumps(config, ensure_ascii=False, separators=(",", ":")),
        "query": semantic_query_payload(query, len(selects)),
        "dataTransforms": data_transforms(transform_selects, projection_ordering),
        "filters": "[]",
    }


def card_visual(
    name: str,
    table: str,
    column: str,
    label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    value_type: str = "whole",
) -> list[dict]:
    alias = f"{name}_src"
    query_ref = f"Sum({table}.{column})"
    return [
        textbox_visual(f"{name}_label", label, x, y - 20, width, 22, z, 10, True, "#5E6872"),
        native_visual(
            name=name,
            visual_type="card",
            table=table,
            alias=alias,
            projections={"Values": [query_ref]},
            selects=[sum_select(alias, table, column)],
            transform_selects=[(label, query_ref, "Values", value_type)],
            x=x,
            y=y,
            width=width,
            height=height,
            z=z + 1,
            color="#FFFFFF",
        ),
    ]


def bar_visual(
    name: str,
    table: str,
    category_column: str,
    value_column: str,
    title: str,
    category_label: str,
    value_label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    visual_type: str = "clusteredColumnChart",
    order_by: str | None = None,
    value_type: str = "decimal",
    color: str = "#1B7F79",
) -> list[dict]:
    alias = f"{name}_src"
    category_ref = f"{table}.{category_column}"
    value_ref = f"Sum({table}.{value_column})"
    return [
        textbox_visual(f"{name}_title", title, x, y - 24, width, 22, z, 11, True, "#17212B"),
        native_visual(
            name=name,
            visual_type=visual_type,
            table=table,
            alias=alias,
            projections={"Category": [category_ref], "Y": [value_ref]},
            selects=[column_select(alias, table, category_column), sum_select(alias, table, value_column)],
            transform_selects=[
                (category_label, category_ref, "Category", "category"),
                (value_label, value_ref, "Y", value_type),
            ],
            x=x,
            y=y,
            width=width,
            height=height,
            z=z + 1,
            order_by=order_by or category_column,
            color=color,
        ),
    ]


def slicer_visual(
    name: str,
    table: str,
    column: str,
    label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
) -> list[dict]:
    alias = f"{name}_src"
    query_ref = f"{table}.{column}"
    return [
        textbox_visual(f"{name}_label", label, x, y - 20, width, 22, z, 10, True, "#5E6872"),
        native_visual(
            name=name,
            visual_type="slicer",
            table=table,
            alias=alias,
            projections={"Values": [query_ref]},
            selects=[column_select(alias, table, column)],
            transform_selects=[(label, query_ref, "Values", "category")],
            x=x,
            y=y,
            width=width,
            height=height,
            z=z + 1,
            order_by=column,
            color="#FFFFFF",
        ),
    ]


def header_visuals(display_name: str) -> list[dict]:
    title, subtitle = PAGE_COPY[display_name]
    return [
        textbox_visual(f"{display_name}_title", title, 54, 34, 1080, 48, 1, 23, True, "#17212B"),
        textbox_visual(f"{display_name}_subtitle", subtitle, 56, 86, 1088, 36, 2, 12, False, "#37414C"),
        textbox_visual(f"{display_name}_accent", "|", 1138, 30, 30, 52, 3, 30, True, "#C5C9CD"),
    ]


def insight_text(name: str, text: str, x: float, y: float, width: float, height: float, z: int, color: str) -> dict:
    return textbox_visual(name, text, x, y, width, height, z, 12, True, color)


def lineage_visuals() -> list[dict]:
    steps = [
        ("Kaggle CSV", 74, "#1B7F79"),
        ("BigQuery Raw", 254, "#2854A3"),
        ("dbt Staging", 434, "#2854A3"),
        ("dbt Mart", 614, "#6D2BD4"),
        ("Power BI DirectQuery", 794, "#B66D12"),
    ]
    visuals: list[dict] = [
        textbox_visual("lineage_title", "Analitik veri akışı", 74, 478, 980, 24, 70, 13, True, "#17212B")
    ]
    for index, (label, x, color) in enumerate(steps, start=1):
        visuals.append(textbox_visual(f"lineage_step_{index}", label, x, 516, 150, 30, 70 + index, 11, True, color))
        if index < len(steps):
            visuals.append(textbox_visual(f"lineage_arrow_{index}", "->", x + 142, 516, 38, 30, 80 + index, 12, True, "#5E6872"))
    return visuals


def page_native_visuals(display_name: str) -> list[dict]:
    visuals = header_visuals(display_name)

    if display_name == "Yönetici Özeti":
        for visual in [
            card_visual("exec_total_txn", "mart_fraud_summary", "total_transactions", "Toplam işlem", 64, 154, 218, 72, 10),
            card_visual("exec_fraud_txn", "mart_fraud_summary", "fraud_transactions", "Sahte işlem", 314, 154, 218, 72, 12),
            card_visual("exec_fraud_rate", "mart_fraud_summary", "fraud_rate", "Baz fraud oranı", 564, 154, 218, 72, 14, "percent"),
            card_visual("exec_identity_rate", "mart_fraud_summary", "identity_coverage_rate", "Identity kapsama", 814, 154, 218, 72, 16, "percent"),
            slicer_visual("exec_product_slicer", "fact_train_transactions", "product_cd", "Ürün filtresi", 1062, 150, 142, 92, 18),
            bar_visual(
                "exec_product_risk",
                "mart_product_device_stats",
                "product_cd",
                "fraud_rate",
                "Ürün kırılımında fraud oranı",
                "Ürün",
                "Fraud oranı",
                74,
                300,
                324,
                210,
                30,
                value_type="percent",
                color="#C6251A",
            ),
            bar_visual(
                "exec_risk_band_rate",
                "mart_risk_band_stats",
                "risk_band",
                "observed_fraud_rate",
                "Risk bandı gözlenen fraud oranı",
                "Risk bandı",
                "Gözlenen fraud oranı",
                456,
                300,
                324,
                210,
                32,
                value_type="percent",
                color="#6D2BD4",
            ),
            bar_visual(
                "exec_amount_risk",
                "mart_amount_bands",
                "amount_band",
                "fraud_rate",
                "Tutar bandına göre risk",
                "Tutar bandı",
                "Fraud oranı",
                838,
                300,
                324,
                210,
                34,
                value_type="percent",
                color="#B66D12",
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            [
                insight_text(
                    "exec_message_1",
                    "Yönetim aksiyonu: Product C, yüksek risk bandı ve uç tutar bantları ilk izleme kuyruğuna alınmalıdır.",
                    84,
                    570,
                    500,
                    42,
                    60,
                    "#C6251A",
                ),
                insight_text(
                    "exec_message_2",
                    "Operasyon prensibi: model çıktısı nihai karar değil, fraud ekibinin inceleme sırasını belirleyen öncelik sinyalidir.",
                    640,
                    570,
                    500,
                    42,
                    61,
                    "#1B7F79",
                ),
            ]
        )

    elif display_name == "Risk Konsantrasyonu":
        for visual in [
            slicer_visual("risk_product_slicer", "fact_train_transactions", "product_cd", "Ürün", 74, 150, 150, 92, 10),
            slicer_visual("risk_band_slicer", "fact_train_transactions", "risk_band", "Risk bandı", 254, 150, 170, 92, 12),
            bar_visual(
                "risk_product_rate",
                "mart_product_device_stats",
                "product_cd",
                "fraud_rate",
                "Ürün bazlı risk ayrışması",
                "Ürün",
                "Fraud oranı",
                74,
                320,
                320,
                220,
                30,
                value_type="percent",
                color="#C6251A",
            ),
            bar_visual(
                "risk_device_rate",
                "mart_product_device_stats",
                "device_type",
                "fraud_rate",
                "Cihaz tipine göre risk",
                "Cihaz tipi",
                "Fraud oranı",
                454,
                320,
                320,
                220,
                32,
                value_type="percent",
                color="#1B7F79",
            ),
            bar_visual(
                "risk_band_rate",
                "mart_risk_band_stats",
                "risk_band",
                "observed_fraud_rate",
                "Risk bandı öncelik sırası",
                "Risk bandı",
                "Gözlenen fraud oranı",
                834,
                320,
                320,
                220,
                34,
                value_type="percent",
                color="#6D2BD4",
            ),
        ]:
            visuals.extend(visual)
        visuals.append(
            insight_text(
                "risk_decision_message",
                "Karar mesajı: Product C ve mobil/identity sinyalleri öncelikli izlenmelidir.",
                76,
                590,
                960,
                38,
                60,
                "#17212B",
            )
        )

    elif display_name == "Tutar ve Zaman Analizi":
        for visual in [
            slicer_visual("amount_band_slicer", "fact_train_transactions", "amount_band", "Tutar bandı", 74, 150, 190, 92, 10),
            bar_visual(
                "amount_band_rate",
                "mart_amount_bands",
                "amount_band",
                "fraud_rate",
                "Tutar bandı fraud oranı",
                "Tutar bandı",
                "Fraud oranı",
                74,
                320,
                330,
                220,
                30,
                value_type="percent",
                color="#B66D12",
            ),
            bar_visual(
                "amount_hour_fraud",
                "fact_train_transactions",
                "transaction_hour",
                "is_fraud",
                "Gün içi sahte işlem adedi",
                "İşlem saati",
                "Sahte işlem adedi",
                464,
                320,
                330,
                220,
                32,
                value_type="whole",
                color="#C6251A",
            ),
            bar_visual(
                "amount_band_volume",
                "fact_train_transactions",
                "amount_band",
                "transaction_amount",
                "Tutar bandı işlem hacmi",
                "Tutar bandı",
                "İşlem tutarı",
                854,
                320,
                330,
                220,
                34,
                value_type="decimal",
                color="#2854A3",
            ),
        ]:
            visuals.extend(visual)
        visuals.append(
            insight_text(
                "amount_decision_message",
                "Yorum: risk yalnızca yüksek tutarlarda artmıyor; düşük tutar bandı ve belirli saat pencereleri ayrı operasyon kuralı gerektiriyor.",
                76,
                590,
                1010,
                38,
                60,
                "#17212B",
            )
        )

    elif display_name == "Ödeme ve Email Segmentleri":
        for visual in [
            slicer_visual(
                "email_domain_slicer",
                "fact_train_transactions",
                "purchaser_email_group",
                "Email grubu",
                74,
                150,
                210,
                92,
                10,
            ),
            bar_visual(
                "payment_network_fraud",
                "fact_train_transactions",
                "card_network",
                "is_fraud",
                "Kart ağına göre sahte işlem",
                "Kart ağı",
                "Sahte işlem adedi",
                74,
                320,
                320,
                220,
                30,
                value_type="whole",
                color="#2854A3",
            ),
            bar_visual(
                "payment_type_fraud",
                "fact_train_transactions",
                "card_type",
                "is_fraud",
                "Kart tipine göre sahte işlem",
                "Kart tipi",
                "Sahte işlem adedi",
                454,
                320,
                320,
                220,
                32,
                value_type="whole",
                color="#1B7F79",
            ),
            bar_visual(
                "email_domain_rate",
                "mart_email_domain_stats",
                "purchaser_email_group",
                "fraud_rate",
                "Email domain fraud oranı",
                "Email grubu",
                "Fraud oranı",
                834,
                320,
                320,
                220,
                34,
                "clusteredBarChart",
                value_type="percent",
                color="#C6251A",
            ),
        ]:
            visuals.extend(visual)
        visuals.append(
            insight_text(
                "payment_decision_message",
                "Segment kararı: kredi kartı ve belirli email domain grupları, product ve tutar segmentleriyle birlikte izlenmelidir.",
                76,
                590,
                1000,
                38,
                60,
                "#17212B",
            )
        )

    elif display_name == "Model Skorlama ve Risk Bantları":
        for visual in [
            slicer_visual("model_risk_slicer", "fact_train_transactions", "risk_band", "Risk bandı", 74, 150, 180, 92, 10),
            bar_visual(
                "model_observed_rate",
                "mart_risk_band_stats",
                "risk_band",
                "observed_fraud_rate",
                "Risk bandı gözlenen fraud oranı",
                "Risk bandı",
                "Gözlenen fraud oranı",
                74,
                320,
                330,
                220,
                30,
                value_type="percent",
                color="#6D2BD4",
            ),
            bar_visual(
                "model_fraud_count",
                "fact_train_transactions",
                "risk_band",
                "is_fraud",
                "Risk bandı sahte işlem hacmi",
                "Risk bandı",
                "Sahte işlem adedi",
                464,
                320,
                330,
                220,
                32,
                value_type="whole",
                color="#C6251A",
            ),
            bar_visual(
                "model_amount_by_band",
                "fact_train_transactions",
                "risk_band",
                "transaction_amount",
                "Risk bandı işlem tutarı",
                "Risk bandı",
                "İşlem tutarı",
                854,
                320,
                330,
                220,
                34,
                value_type="decimal",
                color="#2854A3",
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            [
                insight_text(
                    "model_message_1",
                    "Model yorumu: skor bandı nihai karar değildir; inceleme kapasitesini ölçülebilir kuyruklara böler.",
                    76,
                    585,
                    520,
                    42,
                    60,
                    "#17212B",
                ),
                insight_text(
                    "model_message_2",
                    "Operasyon kullanımı: yüksek ve kritik bantlar hızlı inceleme, düşük bantlar otomatik izleme adayıdır.",
                    650,
                    585,
                    500,
                    42,
                    61,
                    "#1B7F79",
                ),
            ]
        )

    elif display_name == "Veri Kalitesi ve Mimari":
        for visual in [
            bar_visual(
                "quality_missing_rate",
                "mart_feature_missingness",
                "column_family",
                "missing_rate",
                "Feature ailesi eksiklik oranı",
                "Feature ailesi",
                "Eksiklik oranı",
                74,
                266,
                350,
                200,
                30,
                "clusteredBarChart",
                value_type="percent",
                color="#1B7F79",
            ),
            bar_visual(
                "quality_missing_count",
                "mart_feature_missingness",
                "column_family",
                "missing_count",
                "Eksik değer hacmi",
                "Feature ailesi",
                "Eksik değer",
                474,
                266,
                350,
                200,
                32,
                "clusteredBarChart",
                value_type="whole",
                color="#B66D12",
            ),
            card_visual("quality_row_count", "mart_fraud_summary", "total_transactions", "Profil edilen satır", 874, 296, 220, 74, 40),
            card_visual("quality_missing_total", "mart_feature_missingness", "missing_count", "Eksik değer sinyali", 874, 414, 220, 74, 42),
        ]:
            visuals.extend(visual)
        visuals.extend(lineage_visuals())
        visuals.append(
            insight_text(
                "quality_pass_message",
                "Kalite mesajı: dbt build ve BigQuery row-count kontrolleri PASS; rapor katmanı DirectQuery ile mart tablolarına bağlıdır.",
                76,
                604,
                980,
                38,
                90,
                "#17212B",
            )
        )

    return visuals


def apply_final_report_layout(layout: dict) -> dict:
    for section in layout["sections"]:
        section["visualContainers"] = page_native_visuals(section["displayName"])
    return layout


def clean_content_types(raw: bytes) -> bytes:
    namespace = "http://schemas.openxmlformats.org/package/2006/content-types"
    ET.register_namespace("", namespace)
    root = ET.fromstring(raw.decode("utf-8-sig"))

    for child in list(root):
        if child.attrib.get("PartName") == "/SecurityBindings":
            root.remove(child)
        if child.attrib.get("Extension") == "png":
            root.remove(child)

    return ("\ufeff" + ET.tostring(root, encoding="unicode")).encode("utf-8")


def build_pbix() -> None:
    if not BASE_PBIX.exists():
        raise FileNotFoundError(f"Base PBIX not found: {BASE_PBIX}")

    POWERBI_DIR.mkdir(parents=True, exist_ok=True)
    layout = read_layout_template()
    layout = normalize_layout(layout)
    layout = apply_final_report_layout(layout)
    layout_bytes = json.dumps(layout, ensure_ascii=False, separators=(",", ":")).encode("utf-16le")

    with ZipFile(BASE_PBIX, "r") as source:
        entries = {}
        for name in source.namelist():
            if name == "SecurityBindings":
                continue
            if name.startswith("Report/StaticResources/RegisteredResources/") and name.endswith(".png"):
                continue
            entries[name] = source.read(name)

    entries["Report/Layout"] = layout_bytes
    entries["[Content_Types].xml"] = clean_content_types(entries["[Content_Types].xml"])

    tmp = FINAL_PBIX.with_suffix(".pbix.tmp")
    with ZipFile(tmp, "w", compression=ZIP_DEFLATED) as target:
        for name, data in entries.items():
            target.writestr(name, data)
    shutil.move(str(tmp), str(FINAL_PBIX))
    print(f"Power BI v2 report ready: {FINAL_PBIX}")


if __name__ == "__main__":
    build_pbix()
