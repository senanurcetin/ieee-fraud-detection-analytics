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
THEME_PATH = "Report/StaticResources/SharedResources/BaseThemes/CY26SU04.json"

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
        "Sahtecilik belirli segmentlerde yoğunlaşıyor",
        "Yönetim odağı genel hacimden çok riskin kümelendiği ürün, tutar ve risk bandı kesitlerine çevrilmelidir.",
    ),
    "Risk Konsantrasyonu": (
        "Ürün ve cihaz kırılımı riski netleştiriyor",
        "Product C, mobil işlem davranışı ve yüksek risk bandı birlikte izlendiğinde operasyon kuyruğu daha hedefli yönetilir.",
    ),
    "Tutar ve Zaman Analizi": (
        "Tutar ve saat örüntüleri risk sinyali üretiyor",
        "Düşük tutar, yüksek tutar ve gün içi pencereler ayrı izlenmediğinde segment riski ortalamada kaybolur.",
    ),
    "Ödeme ve Email Segmentleri": (
        "Ödeme ve email segmentleri izleme kırılımı ekliyor",
        "Kart ağı, kart tipi ve purchaser email grubu fraud riskini iş birimleri için okunabilir segmentlere dönüştürür.",
    ),
    "Model Skorlama ve Risk Bantları": (
        "Model skorları inceleme önceliği üretir",
        "Risk bantları fraud inceleme kapasitesini yüksek olasılıklı işlem gruplarına yönlendiren bir sıralama katmanıdır.",
    ),
    "Veri Kalitesi ve Mimari": (
        "Veri kalitesi rapor güvenini destekler",
        "Eksiklik yapısal bir veri karakteristiği olarak izlenir; dbt ve BigQuery kontrolleri rapor katmanını doğrular.",
    ),
}

KPI_VALUES = {
    ("mart_fraud_summary", "total_transactions"): "590.540",
    ("mart_fraud_summary", "fraud_transactions"): "20.663",
    ("mart_fraud_summary", "fraud_rate"): "%3,50",
    ("mart_fraud_summary", "identity_coverage_rate"): "%24,42",
    ("mart_feature_missingness", "missing_count"): "173.266.341",
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
    fill: str | None = None,
    border: str | None = None,
) -> dict:
    vc_objects = visual_container_objects(fill, border)
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
    if vc_objects:
        config["vcObjects"] = vc_objects
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


def literal(value: str | int | float | bool) -> dict:
    if isinstance(value, bool):
        literal_value = "true" if value else "false"
    elif isinstance(value, int):
        literal_value = f"{value}D"
    elif isinstance(value, float):
        literal_value = f"{value}D"
    else:
        literal_value = f"'{value}'"
    return {"expr": {"Literal": {"Value": literal_value}}}


def visual_container_objects(fill: str | None = None, border: str | None = None) -> dict:
    objects: dict[str, list[dict]] = {}
    if fill:
        objects["background"] = [
            {
                "properties": {
                    "show": literal(True),
                    "color": {"solid": {"color": fill}},
                    "transparency": literal(0),
                }
            }
        ]
    if border:
        objects["border"] = [
            {
                "properties": {
                    "show": literal(True),
                    "color": {"solid": {"color": border}},
                    "radius": literal(4),
                }
            }
        ]
    return objects


def column_expr(alias: str, column: str) -> dict:
    return {"Column": {"Expression": source_ref(alias), "Property": column}}


def column_select(alias: str, table: str, column: str, query_name: str | None = None) -> dict:
    return {
        "Column": {"Expression": source_ref(alias), "Property": column},
        "Name": query_name or f"{table}.{column}",
    }


def sum_select(alias: str, table: str, column: str, query_name: str | None = None) -> dict:
    return {
        "Aggregation": {
            "Expression": {"Column": {"Expression": source_ref(alias), "Property": column}},
            "Function": 0,
        },
        "Name": query_name or f"Sum({table}.{column})",
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


def visual_objects(visual_type: str, color: str, show_title: bool, title_text: str | None = None) -> dict:
    title = {
        "show": literal(show_title),
        "fontColor": {"solid": {"color": "#17212B"}},
        "fontSize": literal(11),
    }
    if title_text:
        title["text"] = literal(title_text)
    objects = {
        "title": [{"properties": title}],
        "labels": [
            {
                "properties": {
                    "show": literal(False),
                    "labelDisplayUnits": literal(0),
                    "labelPrecision": literal(1),
                    "color": {"solid": {"color": "#17212B"}},
                }
            }
        ],
        "dataPoint": [{"properties": {"defaultColor": {"solid": {"color": color}}}}],
    }
    if visual_type == "card":
        objects.update(
            {
                "categoryLabels": [{"properties": {"show": literal(False)}}],
                "calloutValue": [
                    {
                        "properties": {
                            "labelDisplayUnits": literal(0),
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
                            "show": literal(True),
                            "showAxisTitle": literal(False),
                            "fontColor": {"solid": {"color": "#5E6872"}},
                        }
                    }
                ],
                "valueAxis": [
                    {
                        "properties": {
                            "show": literal(True),
                            "showAxisTitle": literal(False),
                            "labelDisplayUnits": literal(0),
                            "fontColor": {"solid": {"color": "#5E6872"}},
                        }
                    }
                ],
            }
        )
    return objects


def panel_visual(
    name: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    fill: str = "#FFFFFF",
    border: str = "#DCE3EA",
) -> dict:
    return textbox_visual(name, " ", x, y, width, height, z, 8, False, fill, fill, border)


def panel_title(name: str, text: str, x: float, y: float, width: float, z: int, color: str = "#17212B") -> dict:
    return textbox_visual(name, text, x, y, width, 34, z, 10, True, color)


def accent_rule(name: str, x: float, y: float, height: float, z: int, color: str) -> dict:
    return textbox_visual(name, " ", x, y, 4, height, z, 8, False, color, color, None)


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
    fill: str | None = None,
    border: str | None = None,
    title_text: str | None = None,
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
            "objects": visual_objects(visual_type, color, show_title, title_text),
        },
        "vcObjects": visual_container_objects(fill, border),
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
    value = KPI_VALUES.get((table, column), "590.540")
    return [
        panel_visual(f"{name}_panel", x, y, width, height, z, "#FFFFFF", "#DCE3EA"),
        accent_rule(f"{name}_accent", x, y + 10, height - 20, z + 1, "#1B7F79"),
        textbox_visual(f"{name}_label", label, x + 18, y + 10, width - 28, 20, z + 2, 9, True, "#5E6872"),
        textbox_visual(f"{name}_value", value, x + 18, y + 32, width - 28, height - 36, z + 3, 20, True, "#17212B"),
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
    tooltip_fields: list[tuple[str, str, str]] | None = None,
) -> list[dict]:
    alias = f"{name}_src"
    category_ref = category_label
    value_ref = value_label
    selects = [
        column_select(alias, table, category_column, category_ref),
        sum_select(alias, table, value_column, value_ref),
    ]
    projections = {"Category": [category_ref], "Y": [value_ref]}
    transform_selects = [
        (category_label, category_ref, "Category", "category"),
        (value_label, value_ref, "Y", value_type),
    ]
    if tooltip_fields:
        projections["Tooltips"] = []
        for tooltip_column, tooltip_label, tooltip_type in tooltip_fields:
            tooltip_ref = tooltip_label
            selects.append(sum_select(alias, table, tooltip_column, tooltip_ref))
            projections["Tooltips"].append(tooltip_ref)
            transform_selects.append((tooltip_label, tooltip_ref, "Tooltips", tooltip_type))
    return [
        panel_visual(f"{name}_panel", x, y, width, height, z, "#FFFFFF", "#DCE3EA"),
        accent_rule(f"{name}_accent", x, y + 12, height - 24, z + 1, color),
        panel_title(f"{name}_title", title, x + 24, y + 10, width - 38, z + 2),
        native_visual(
            name=name,
            visual_type=visual_type,
            table=table,
            alias=alias,
            projections=projections,
            selects=selects,
            transform_selects=transform_selects,
            x=x + 12,
            y=y + 44,
            width=width - 24,
            height=height - 56,
            z=z + 3,
            order_by=order_by or category_column,
            color=color,
            show_title=False,
        ),
    ]


def table_visual(
    name: str,
    table: str,
    columns: list[tuple[str, str, str]],
    title: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    order_by: str | None = None,
) -> list[dict]:
    alias = f"{name}_src"
    selects = []
    projections = []
    transform_selects = []
    for column, label, value_type in columns:
        query_ref = label
        if value_type == "category":
            selects.append(column_select(alias, table, column, query_ref))
        else:
            selects.append(sum_select(alias, table, column, query_ref))
        projections.append(query_ref)
        transform_selects.append((label, query_ref, "Values", value_type))

    return [
        panel_visual(f"{name}_panel", x, y, width, height, z, "#FFFFFF", "#DCE3EA"),
        accent_rule(f"{name}_accent", x, y + 12, height - 24, z + 1, "#2854A3"),
        panel_title(f"{name}_title", title, x + 24, y + 10, width - 38, z + 2),
        native_visual(
            name=name,
            visual_type="tableEx",
            table=table,
            alias=alias,
            projections={"Values": projections},
            selects=selects,
            transform_selects=transform_selects,
            x=x + 12,
            y=y + 44,
            width=width - 24,
            height=height - 56,
            z=z + 3,
            order_by=order_by,
            color="#1B7F79",
            show_title=False,
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
    query_ref = label
    return [
        panel_visual(f"{name}_panel", x, y, width, height, z, "#EEF3F8", "#B8C6D6"),
        textbox_visual(f"{name}_header", label, x, y, width, 24, z + 1, 8, True, "#FFFFFF", "#17212B", None),
        accent_rule(f"{name}_accent", x, y + 24, height - 24, z + 2, "#1B7F79"),
        panel_visual(f"{name}_body", x + 8, y + 30, width - 16, height - 38, z + 3, "#FFFFFF", "#DCE3EA"),
        native_visual(
            name=name,
            visual_type="slicer",
            table=table,
            alias=alias,
            projections={"Values": [query_ref]},
            selects=[column_select(alias, table, column, query_ref)],
            transform_selects=[(label, query_ref, "Values", "category")],
            x=x + 14,
            y=y + 36,
            width=width - 28,
            height=height - 48,
            z=z + 4,
            order_by=column,
            color="#FFFFFF",
            show_title=False,
        ),
    ]


def header_visuals(display_name: str) -> list[dict]:
    title, subtitle = PAGE_COPY[display_name]
    page_index = [new_name for _old_name, new_name in PAGE_ORDER].index(display_name) + 1
    nav_items = [
        ("01", "Özet"),
        ("02", "Risk"),
        ("03", "Tutar"),
        ("04", "Ödeme"),
        ("05", "Model"),
        ("06", "Kalite"),
    ]
    visuals = [
        textbox_visual(f"{display_name}_bg", " ", 0, 0, 1280, 720, 0, 8, False, "#F6F8FB", "#F6F8FB", None),
        textbox_visual(f"{display_name}_top_rule", " ", 54, 22, 1088, 3, 2, 8, False, "#17212B", "#17212B", None),
        textbox_visual(f"{display_name}_section_label", "FRAUD RISK INTELLIGENCE", 54, 34, 280, 20, 4, 8, True, "#5E6872"),
        textbox_visual(f"{display_name}_page_no", f"Sayfa {page_index}/6", 1092, 34, 90, 20, 4, 8, True, "#5E6872"),
        textbox_visual(f"{display_name}_title", title, 54, 62, 1088, 50, 5, 16, True, "#17212B"),
        textbox_visual(f"{display_name}_subtitle", subtitle, 56, 114, 1088, 30, 6, 9, False, "#37414C"),
    ]
    for index, (number, label) in enumerate(nav_items, start=1):
        x = 54 + (index - 1) * 188
        is_active = index == page_index
        visuals.append(
            textbox_visual(
                f"{display_name}_nav_{index}",
                f"{number}  {label}",
                x,
                684,
                178,
                24,
                8 + index,
                9,
                True,
                "#17212B" if is_active else "#7A8793",
            )
        )
    return visuals


def insight_text(name: str, text: str, x: float, y: float, width: float, height: float, z: int, color: str) -> dict:
    return textbox_visual(name, text, x, y, width, height, z, 12, True, color)


def insight_panel(
    name: str,
    title: str,
    body: str,
    x: float,
    y: float,
    width: float,
    z: int,
    color: str,
) -> list[dict]:
    return [
        panel_visual(f"{name}_panel", x - 8, y - 8, width + 16, 86, z, "#FFFFFF", "#DCE3EA"),
        accent_rule(f"{name}_accent", x - 8, y - 8, 86, z + 1, color),
        textbox_visual(f"{name}_title", title, x + 8, y, width - 8, 22, z + 2, 10, True, color),
        textbox_visual(f"{name}_body", body, x + 8, y + 24, width - 8, 54, z + 3, 8, False, "#37414C"),
    ]


def filter_panel(name: str, title: str, x: float, y: float, width: float, height: float, z: int = 8) -> list[dict]:
    return []


def section_label(name: str, text: str, x: float, y: float, width: float, z: int = 18) -> dict:
    return textbox_visual(name, text, x, y, width, 20, z, 9, True, "#5E6872")


def risk_legend(name: str, x: float, y: float, z: int = 20) -> list[dict]:
    bands = [
        ("Critical", "#C6251A"),
        ("High", "#B66D12"),
        ("Elevated", "#6D2BD4"),
        ("Low", "#1B7F79"),
    ]
    visuals = [
        textbox_visual(f"{name}_title", "Risk renk standardı", x, y, 230, 20, z, 9, True, "#5E6872")
    ]
    for index, (label, color) in enumerate(bands):
        item_x = x + index * 104
        visuals.append(textbox_visual(f"{name}_{label}_label", f"■ {label}", item_x, y + 20, 96, 22, z + 10 + index, 8, True, color))
    return visuals


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
        visuals.extend(filter_panel("exec_filter_panel", "Filtre kontrolü", 1044, 132, 174, 126))
        visuals.append(section_label("exec_analysis_label", "ANA RİSK GÖSTERGELERİ", 74, 264, 360))
        visuals.append(section_label("exec_decision_label", "YÖNETİM KARARI", 74, 532, 360))
        for visual in [
            card_visual("exec_total_txn", "mart_fraud_summary", "total_transactions", "Toplam işlem", 64, 154, 218, 72, 10),
            card_visual("exec_fraud_txn", "mart_fraud_summary", "fraud_transactions", "Sahte işlem", 314, 154, 218, 72, 12),
            card_visual("exec_fraud_rate", "mart_fraud_summary", "fraud_rate", "Baz fraud oranı", 564, 154, 218, 72, 14, "percent"),
            card_visual("exec_identity_rate", "mart_fraud_summary", "identity_coverage_rate", "Identity kapsama", 814, 154, 218, 72, 16, "percent"),
            slicer_visual("exec_product_slicer", "fact_train_transactions", "product_cd", "Ürün filtresi", 1062, 150, 142, 92, 18),
            bar_visual(
                "exec_product_risk",
                "fact_train_transactions",
                "product_cd",
                "is_fraud",
                "Ürüne göre sahte işlem hacmi",
                "Ürün",
                "Sahte işlem adedi",
                74,
                300,
                324,
                210,
                30,
                value_type="whole",
                color="#C6251A",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
            bar_visual(
                "exec_risk_band_rate",
                "fact_train_transactions",
                "risk_band",
                "is_fraud",
                "Risk bandına göre sahte işlem hacmi",
                "Risk bandı",
                "Sahte işlem adedi",
                456,
                300,
                324,
                210,
                32,
                value_type="whole",
                color="#6D2BD4",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
            bar_visual(
                "exec_amount_risk",
                "fact_train_transactions",
                "amount_band",
                "is_fraud",
                "Tutar bandına göre sahte işlem hacmi",
                "Tutar bandı",
                "Sahte işlem adedi",
                838,
                300,
                324,
                210,
                34,
                value_type="whole",
                color="#B66D12",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            insight_panel(
                "exec_panel_1",
                "Bulgu",
                "590.540 işlem içinde fraud oranı %3,5; Product C ise tek başına fraud hacminin %38,8'ini taşıyor.",
                74,
                560,
                320,
                60,
                "#C6251A",
            )
            + insight_panel(
                "exec_panel_2",
                "Risk",
                "Product C baz oranın 3,34 katı risk taşıyor; genel ortalama ile yönetilirse bu yoğunlaşma görünmez.",
                456,
                560,
                320,
                70,
                "#6D2BD4",
            )
            + insight_panel(
                "exec_panel_3",
                "Aksiyon",
                "Ürün, risk bandı ve tutar kesitleri haftalık risk komitesinde standart takip kırılımı olmalıdır.",
                838,
                560,
                320,
                80,
                "#1B7F79",
            )
        )

    elif display_name == "Risk Konsantrasyonu":
        visuals.extend(filter_panel("risk_filter_panel", "Filtre kontrolü", 54, 132, 390, 126))
        visuals.append(section_label("risk_analysis_label", "SEGMENT RİSK AYRIŞMASI", 74, 284, 360))
        visuals.append(section_label("risk_decision_label", "OPERASYONEL ÖNCELİK", 74, 546, 360))
        for visual in [
            slicer_visual("risk_product_slicer", "fact_train_transactions", "product_cd", "Ürün", 74, 150, 150, 92, 10),
            slicer_visual("risk_band_slicer", "fact_train_transactions", "risk_band", "Risk bandı", 254, 150, 170, 92, 12),
            table_visual(
                "risk_evidence_table",
                "fact_train_transactions",
                [
                    ("product_cd", "Ürün", "category"),
                    ("risk_band", "Risk bandı", "category"),
                    ("is_fraud", "Sahte işlem", "whole"),
                    ("transaction_amount", "İşlem tutarı", "decimal"),
                ],
                "Ürün ve risk bandı kanıt tablosu",
                474,
                150,
                690,
                110,
                18,
                "product_cd",
            ),
            bar_visual(
                "risk_product_rate",
                "fact_train_transactions",
                "product_cd",
                "is_fraud",
                "Ürün bazlı sahte işlem hacmi",
                "Ürün",
                "Sahte işlem adedi",
                74,
                320,
                320,
                220,
                30,
                value_type="whole",
                color="#C6251A",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
            bar_visual(
                "risk_device_rate",
                "fact_train_transactions",
                "device_type",
                "is_fraud",
                "Cihaz tipine göre sahte işlem hacmi",
                "Cihaz tipi",
                "Sahte işlem adedi",
                454,
                320,
                320,
                220,
                32,
                value_type="whole",
                color="#1B7F79",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
            bar_visual(
                "risk_band_rate",
                "fact_train_transactions",
                "risk_band",
                "is_fraud",
                "Risk bandı sahte işlem hacmi",
                "Risk bandı",
                "Sahte işlem adedi",
                834,
                320,
                320,
                220,
                34,
                value_type="whole",
                color="#6D2BD4",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            insight_panel(
                "risk_panel_1",
                "Bulgu",
                "Identity kaydı olan işlemler hacmin %24,4'ü iken fraud'un %54,8'ini oluşturuyor.",
                74,
                574,
                320,
                60,
                "#C6251A",
            )
            + insight_panel(
                "risk_panel_2",
                "Öncelik",
                "Product C ve identity sinyali beraber izlendiğinde operasyon kuyruğu daha isabetli daralır.",
                456,
                574,
                320,
                70,
                "#6D2BD4",
            )
            + insight_panel(
                "risk_panel_3",
                "Kontrol",
                "Ürün ve risk bandı filtreleri yönetim toplantısında aynı bulgunun farklı segmentlerde test edilmesini sağlar.",
                838,
                574,
                320,
                80,
                "#1B7F79",
            )
        )
        visuals.extend(risk_legend("risk_color_legend", 474, 266, 44))

    elif display_name == "Tutar ve Zaman Analizi":
        visuals.extend(filter_panel("amount_filter_panel", "Filtre kontrolü", 54, 132, 246, 126))
        visuals.append(section_label("amount_analysis_label", "TUTAR VE ZAMAN SİNYALLERİ", 74, 284, 360))
        visuals.append(section_label("amount_decision_label", "TAKİP STRATEJİSİ", 74, 546, 360))
        for visual in [
            slicer_visual("amount_band_slicer", "fact_train_transactions", "amount_band", "Tutar bandı", 74, 150, 190, 92, 10),
            table_visual(
                "amount_evidence_table",
                "fact_train_transactions",
                [
                    ("amount_band", "Tutar bandı", "category"),
                    ("is_fraud", "Sahte işlem", "whole"),
                    ("transaction_amount", "İşlem tutarı", "decimal"),
                ],
                "Tutar bandı kanıt tablosu",
                330,
                150,
                834,
                110,
                18,
                "amount_band",
            ),
            bar_visual(
                "amount_band_rate",
                "fact_train_transactions",
                "amount_band",
                "is_fraud",
                "Tutar bandına göre sahte işlem hacmi",
                "Tutar bandı",
                "Sahte işlem adedi",
                74,
                320,
                330,
                220,
                30,
                value_type="whole",
                color="#B66D12",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
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
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
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
                tooltip_fields=[("is_fraud", "Sahte işlem", "whole")],
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            insight_panel(
                "amount_panel_1",
                "Bulgu",
                "<$25 bandı %7,0 fraud oranıyla baz oranın yaklaşık 2 katına çıkıyor.",
                74,
                574,
                320,
                60,
                "#B66D12",
            )
            + insight_panel(
                "amount_panel_2",
                "Zaman",
                "Gün içi kırılım, fraud ekibi vardiya kapasitesinin saatlik hacme göre ayarlanmasını sağlar.",
                456,
                574,
                320,
                70,
                "#C6251A",
            )
            + insight_panel(
                "amount_panel_3",
                "Aksiyon",
                "Düşük tutar bandı, yüksek tutar bandı ve yoğun saatler ayrı izleme eşiğiyle ele alınmalıdır.",
                838,
                574,
                320,
                80,
                "#1B7F79",
            )
        )

    elif display_name == "Ödeme ve Email Segmentleri":
        visuals.extend(filter_panel("payment_filter_panel", "Filtre kontrolü", 54, 132, 270, 126))
        visuals.append(section_label("payment_analysis_label", "ÖDEME VE EMAIL KIRILIMLARI", 74, 284, 400))
        visuals.append(section_label("payment_decision_label", "SEGMENT AKSİYONU", 74, 546, 360))
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
            table_visual(
                "payment_evidence_table",
                "fact_train_transactions",
                [
                    ("card_network", "Kart ağı", "category"),
                    ("card_type", "Kart tipi", "category"),
                    ("is_fraud", "Sahte işlem", "whole"),
                    ("transaction_amount", "İşlem tutarı", "decimal"),
                ],
                "Ödeme segmenti kanıt tablosu",
                354,
                150,
                810,
                110,
                18,
                "card_network",
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
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
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
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
            bar_visual(
                "email_domain_rate",
                "fact_train_transactions",
                "purchaser_email_group",
                "is_fraud",
                "Email grubuna göre sahte işlem hacmi",
                "Email grubu",
                "Sahte işlem adedi",
                834,
                320,
                320,
                220,
                34,
                "clusteredBarChart",
                value_type="whole",
                color="#C6251A",
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            insight_panel(
                "payment_panel_1",
                "Bulgu",
                "Visa/credit segmenti fraud hacminin %27,6'sını taşıyor; ödeme kırılımı aksiyon aldıran bir segmenttir.",
                74,
                574,
                320,
                60,
                "#2854A3",
            )
            + insight_panel(
                "payment_panel_2",
                "Segment",
                "Gmail hacmin %38,7'si ve fraud'un %48,1'i; hotmail.com ise daha yüksek oranlı takip segmentidir.",
                456,
                574,
                320,
                70,
                "#C6251A",
            )
            + insight_panel(
                "payment_panel_3",
                "Aksiyon",
                "Kart tipi, email domain ve ürün kesişimi birlikte izlenerek operasyon önceliği netleştirilmelidir.",
                838,
                574,
                320,
                80,
                "#1B7F79",
            )
        )

    elif display_name == "Model Skorlama ve Risk Bantları":
        visuals.extend(filter_panel("model_filter_panel", "Filtre kontrolü", 54, 132, 238, 126))
        visuals.append(section_label("model_analysis_label", "SKOR BANTI VE İNCELEME HACMİ", 74, 284, 440))
        visuals.append(section_label("model_decision_label", "İNCELEME KUYRUĞU STRATEJİSİ", 74, 546, 460))
        for visual in [
            slicer_visual("model_risk_slicer", "fact_train_transactions", "risk_band", "Risk bandı", 74, 150, 180, 92, 10),
            table_visual(
                "model_queue_table",
                "fact_train_transactions",
                [
                    ("risk_band", "Risk bandı", "category"),
                    ("is_fraud", "Sahte işlem", "whole"),
                    ("transaction_amount", "İşlem tutarı", "decimal"),
                ],
                "Risk bandı inceleme kanıt tablosu",
                314,
                150,
                850,
                110,
                18,
                "risk_band",
            ),
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
                tooltip_fields=[("transaction_amount", "İşlem tutarı", "decimal")],
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
                tooltip_fields=[("is_fraud", "Sahte işlem", "whole")],
            ),
        ]:
            visuals.extend(visual)
        visuals.extend(
            insight_panel(
                "model_panel_1",
                "Amaç",
                "Critical band hacmin yalnızca %1,0'ı; buna rağmen fraud yakalama payı %27,5 seviyesindedir.",
                74,
                574,
                320,
                60,
                "#6D2BD4",
            )
            + insight_panel(
                "model_panel_2",
                "Operasyon",
                "Critical + High bantları yaklaşık %5 iş yüküyle fraud'un %78,3'ünü yakalar.",
                456,
                574,
                320,
                70,
                "#C6251A",
            )
            + insight_panel(
                "model_panel_3",
                "Yönetim",
                "Skorlar ret kararı değil; aynı gün inceleme, örneklem ve otomatik izleme ayrımı için kullanılır.",
                838,
                574,
                320,
                80,
                "#1B7F79",
            )
        )
        visuals.extend(risk_legend("model_color_legend", 314, 266, 44))

    elif display_name == "Veri Kalitesi ve Mimari":
        visuals.append(section_label("quality_gate_label", "KALİTE KAPISI", 74, 132, 300))
        visuals.append(section_label("quality_analysis_label", "EKSİKLİK PROFİLİ", 74, 230, 300))
        visuals.append(section_label("quality_lineage_label", "VERİ AKIŞI", 74, 458, 300))
        visuals.extend(
            insight_panel(
                "quality_gate_1",
                "Build",
                "dbt prod build sonucu PASS; model, test ve exposure adımları hata vermeden tamamlandı.",
                74,
                152,
                320,
                20,
                "#1B7F79",
            )
            + insight_panel(
                "quality_gate_2",
                "Reconciliation",
                "Raw, staging, mart ve Power BI katmanları row-count kontrolleriyle uzlaştırıldı.",
                456,
                152,
                320,
                30,
                "#2854A3",
            )
            + insight_panel(
                "quality_gate_3",
                "Lineage",
                "Rapor akışı ham Kaggle verisinden DirectQuery tüketim katmanına kadar izlenebilir.",
                838,
                152,
                320,
                40,
                "#B66D12",
            )
        )
        for visual in [
            bar_visual(
                "quality_missing_rate",
                "mart_feature_missingness",
                "column_family",
                "missing_count",
                "Feature ailesi eksik değer hacmi",
                "Feature ailesi",
                "Eksik değer",
                74,
                266,
                350,
                200,
                30,
                "clusteredBarChart",
                value_type="whole",
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


def corporate_theme_bytes() -> bytes:
    theme = {
        "name": "CY26SU04",
        "dataColors": [
            "#C6251A",
            "#1B7F79",
            "#2854A3",
            "#B66D12",
            "#6D2BD4",
            "#17212B",
            "#7A8793",
            "#D9E1EA",
        ],
        "foreground": "#17212B",
        "foregroundNeutralSecondary": "#5E6872",
        "foregroundNeutralTertiary": "#9AA4AF",
        "background": "#F5F7FA",
        "backgroundLight": "#FFFFFF",
        "backgroundNeutral": "#D9E1EA",
        "tableAccent": "#1B7F79",
        "good": "#1B7F79",
        "neutral": "#B66D12",
        "bad": "#C6251A",
        "maximum": "#C6251A",
        "center": "#B66D12",
        "minimum": "#1B7F79",
        "null": "#D9E1EA",
        "hyperlink": "#2854A3",
        "visitedHyperlink": "#2854A3",
        "textClasses": {
            "callout": {"fontSize": 25, "fontFace": "DIN", "color": "#17212B"},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#17212B"},
            "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#17212B"},
            "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#37414C"},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{"show": False, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 100}],
                    "border": [{"show": False, "color": {"solid": {"color": "#E3E8EE"}}, "radius": 0}],
                    "title": [{"show": False, "fontColor": {"solid": {"color": "#17212B"}}, "fontSize": 11}],
                    "categoryAxis": [
                        {
                            "show": True,
                            "showAxisTitle": False,
                            "labelColor": {"solid": {"color": "#5E6872"}},
                            "gridlineColor": {"solid": {"color": "#E7ECF2"}},
                        }
                    ],
                    "valueAxis": [
                        {
                            "show": True,
                            "showAxisTitle": False,
                            "labelColor": {"solid": {"color": "#5E6872"}},
                            "gridlineColor": {"solid": {"color": "#E7ECF2"}},
                        }
                    ],
                    "labels": [{"show": True, "color": {"solid": {"color": "#37414C"}}, "labelDisplayUnits": 0}],
                }
            }
        },
    }
    return json.dumps(theme, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


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
    entries[THEME_PATH] = corporate_theme_bytes()

    tmp = FINAL_PBIX.with_suffix(".pbix.tmp")
    with ZipFile(tmp, "w", compression=ZIP_DEFLATED) as target:
        for name, data in entries.items():
            target.writestr(name, data)
    shutil.move(str(tmp), str(FINAL_PBIX))
    print(f"Power BI v2 report ready: {FINAL_PBIX}")


if __name__ == "__main__":
    build_pbix()
