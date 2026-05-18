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
ASSET_DIR = POWERBI_DIR / "assets"
FINAL_PBIX = POWERBI_DIR / "fraud_project_v2.pbix"

PAGE_ORDER = [
    ("Yonetici Ozeti", "Yönetici Özeti"),
    ("Urun Identity", "Risk Konsantrasyonu"),
    ("Tutar Zaman", "Tutar ve Zaman Analizi"),
    ("Odeme Email", "Ödeme ve Email Segmentleri"),
    ("Model Riski", "Model Skorlama ve Risk Bantları"),
    ("Veri Kalitesi", "Veri Kalitesi ve Mimari"),
]

PAGE_IMAGE_LAYOUTS = {
    "Yönetici Özeti": [
        ("21_executive_decision_matrix.png", 78, 544, 1080, 130),
    ],
    "Risk Konsantrasyonu": [
        ("18_segment_watchlist.png", 648, 398, 520, 244),
    ],
    "Tutar ve Zaman Analizi": [
        ("14_amount_distribution.png", 686, 398, 470, 242),
    ],
    "Ödeme ve Email Segmentleri": [
        ("12_card_payment_heatmap.png", 58, 360, 500, 282),
        ("21_executive_decision_matrix.png", 628, 526, 520, 120),
    ],
    "Model Skorlama ve Risk Bantları": [
        ("05_feature_importance.png", 58, 404, 520, 244),
        ("22_review_strategy_matrix.png", 650, 404, 500, 244),
    ],
    "Veri Kalitesi ve Mimari": [
        ("25_dbt_quality_gate.png", 62, 128, 1090, 168),
        ("09_architecture.png", 654, 392, 500, 250),
    ],
}

REQUIRED_RESOURCE_ITEMS = sorted({asset for placements in PAGE_IMAGE_LAYOUTS.values() for asset, *_ in placements})


def read_layout_template() -> tuple[dict, dict[str, bytes]]:
    if not LAYOUT_TEMPLATE.exists():
        raise FileNotFoundError(f"Layout template not found: {LAYOUT_TEMPLATE}")

    resources: dict[str, bytes] = {}
    with ZipFile(LAYOUT_TEMPLATE, "r") as zf:
        layout = json.loads(zf.read("Report/Layout").decode("utf-16le"))
        for name in zf.namelist():
            if name.startswith("Report/StaticResources/"):
                resources[name] = zf.read(name)
    return layout, resources


def normalize_layout(layout: dict) -> dict:
    source_sections = {section["displayName"]: section for section in layout["sections"]}
    sections = []
    for ordinal, (old_name, new_name) in enumerate(PAGE_ORDER):
        section = source_sections[old_name]
        section["displayName"] = new_name
        section["ordinal"] = ordinal
        section["name"] = f"ReportSection{ordinal}"
        sections.append(section)
    layout["sections"] = sections
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


def image_visual(name: str, item_name: str, x: float, y: float, width: float, height: float, z: int) -> dict:
    config = {
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
    return {
        "x": x,
        "y": y,
        "z": z,
        "width": width,
        "height": height,
        "config": json.dumps(config, ensure_ascii=False, separators=(",", ":")),
        "filters": "[]",
    }


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


def data_transforms(selects: list[tuple[str, str, str, str]], projection_ordering: dict[str, list[int]]) -> str:
    metadata = []
    select_payload = []
    for display_name, query_name, role, value_type in selects:
        type_code = 2048 if value_type == "category" else 259
        metadata.append({"Restatement": display_name, "Name": query_name, "Type": type_code})
        select_payload.append(
            {
                "displayName": display_name,
                "queryName": query_name,
                "roles": {role: True},
                "type": {"category": None} if value_type == "category" else {"numeric": True},
            }
        )
    payload = {
        "selects": select_payload,
        "projectionOrdering": projection_ordering,
        "queryMetadata": {"Select": metadata},
        "visualElements": [],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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
    title: str | None = None,
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
            "objects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title or name}'"}}},
                            "fontColor": {"solid": {"color": "#17212B"}},
                            "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
                        }
                    }
                ],
                "categoryAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "valueAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
            },
        },
    }
    projection_ordering = {
        role: [
            next(index for index, (_display, query_ref, transform_role, _value_type) in enumerate(transform_selects) if query_ref == query_name and transform_role == role)
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
) -> dict:
    alias = f"{name}_src"
    query_ref = f"Sum({table}.{column})"
    return native_visual(
        name=name,
        visual_type="card",
        table=table,
        alias=alias,
        projections={"Values": [query_ref]},
        selects=[sum_select(alias, table, column)],
        transform_selects=[(label, query_ref, "Values", "numeric")],
        x=x,
        y=y,
        width=width,
        height=height,
        z=z,
        title=label,
    )


def bar_visual(
    name: str,
    table: str,
    category_column: str,
    value_column: str,
    category_label: str,
    value_label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    visual_type: str = "clusteredColumnChart",
    order_by: str | None = None,
) -> dict:
    alias = f"{name}_src"
    category_ref = f"{table}.{category_column}"
    value_ref = f"Sum({table}.{value_column})"
    return native_visual(
        name=name,
        visual_type=visual_type,
        table=table,
        alias=alias,
        projections={"Category": [category_ref], "Y": [value_ref]},
        selects=[column_select(alias, table, category_column), sum_select(alias, table, value_column)],
        transform_selects=[(category_label, category_ref, "Category", "category"), (value_label, value_ref, "Y", "numeric")],
        x=x,
        y=y,
        width=width,
        height=height,
        z=z,
        order_by=order_by or category_column,
        title=value_label,
    )


def line_visual(
    name: str,
    table: str,
    category_column: str,
    value_column: str,
    category_label: str,
    value_label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
) -> dict:
    return bar_visual(
        name=name,
        table=table,
        category_column=category_column,
        value_column=value_column,
        category_label=category_label,
        value_label=value_label,
        x=x,
        y=y,
        width=width,
        height=height,
        z=z,
        visual_type="lineChart",
        order_by=category_column,
    )


def table_visual(
    name: str,
    table: str,
    columns: list[tuple[str, str, str]],
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    order_by: str | None = None,
) -> dict:
    alias = f"{name}_src"
    selects = []
    projections = []
    transform_selects = []
    for column, label, value_type in columns:
        if value_type == "numeric":
            query_ref = f"Sum({table}.{column})"
            selects.append(sum_select(alias, table, column))
        else:
            query_ref = f"{table}.{column}"
            selects.append(column_select(alias, table, column))
        projections.append(query_ref)
        transform_selects.append((label, query_ref, "Values", value_type))
    return native_visual(
        name=name,
        visual_type="tableEx",
        table=table,
        alias=alias,
        projections={"Values": projections},
        selects=selects,
        transform_selects=transform_selects,
        x=x,
        y=y,
        width=width,
        height=height,
        z=z,
        order_by=order_by,
        title=name,
    )


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
) -> dict:
    alias = f"{name}_src"
    query_ref = f"{table}.{column}"
    return native_visual(
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
        z=z,
        order_by=column,
        title=label,
    )


def main_page_native_visuals(display_name: str) -> list[dict]:
    if display_name == "Yönetici Özeti":
        return [
            card_visual("exec_total_txn", "mart_fraud_summary", "total_transactions", "Toplam işlem", 54, 120, 230, 78, 110),
            card_visual("exec_fraud_txn", "mart_fraud_summary", "fraud_transactions", "Sahte işlem", 304, 120, 230, 78, 111),
            card_visual("exec_fraud_rate", "mart_fraud_summary", "fraud_rate", "Baz sahtecilik oranı", 554, 120, 230, 78, 112),
            card_visual("exec_identity_rate", "mart_fraud_summary", "identity_coverage_rate", "Identity kapsama", 804, 120, 230, 78, 113),
            slicer_visual("exec_product_slicer", "fact_train_transactions", "product_cd", "Ürün filtresi", 1054, 120, 130, 78, 114),
            bar_visual(
                "exec_product_risk",
                "mart_product_device_stats",
                "product_cd",
                "fraud_rate",
                "Ürün",
                "Ürün bazlı fraud oranı",
                54,
                228,
                330,
                230,
                115,
            ),
            bar_visual(
                "exec_risk_band_lift",
                "mart_risk_band_stats",
                "risk_band",
                "lift",
                "Risk bandı",
                "Risk bandı lift",
                430,
                228,
                330,
                230,
                116,
            ),
            table_visual(
                "exec_risk_queue",
                "mart_risk_band_stats",
                [
                    ("risk_band", "Risk bandı", "category"),
                    ("review_priority", "Öncelik", "category"),
                    ("transaction_count", "İşlem", "numeric"),
                    ("observed_fraud_rate", "Fraud oranı", "numeric"),
                    ("expected_fraud_capture", "Yakalama payı", "numeric"),
                ],
                806,
                228,
                372,
                230,
                117,
                "band_rank",
            ),
        ]

    if display_name == "Risk Konsantrasyonu":
        return [
            slicer_visual("risk_product_slicer", "fact_train_transactions", "product_cd", "Ürün", 54, 118, 130, 72, 110),
            slicer_visual("risk_band_slicer", "fact_train_transactions", "risk_band", "Risk bandı", 204, 118, 150, 72, 111),
            table_visual(
                "risk_product_device_table",
                "mart_product_device_stats",
                [
                    ("product_cd", "Ürün", "category"),
                    ("device_type", "Cihaz", "category"),
                    ("transaction_count", "İşlem", "numeric"),
                    ("fraud_rate", "Fraud oranı", "numeric"),
                    ("lift", "Lift", "numeric"),
                    ("fraud_share", "Fraud payı", "numeric"),
                ],
                54,
                210,
                560,
                180,
                112,
                "product_cd",
            ),
            bar_visual(
                "risk_product_lift",
                "mart_product_device_stats",
                "product_cd",
                "lift",
                "Ürün",
                "Ürün ve cihaz birleşik lift",
                654,
                118,
                250,
                250,
                113,
            ),
            bar_visual(
                "risk_device_rate",
                "mart_product_device_stats",
                "device_type",
                "fraud_rate",
                "Cihaz",
                "Cihaz kırılımı fraud oranı",
                930,
                118,
                250,
                250,
                114,
            ),
            table_visual(
                "risk_band_capture_table",
                "mart_risk_band_stats",
                [
                    ("risk_band", "Risk bandı", "category"),
                    ("transaction_count", "İşlem", "numeric"),
                    ("observed_fraud_rate", "Fraud oranı", "numeric"),
                    ("lift", "Lift", "numeric"),
                    ("expected_fraud_capture", "Yakalama payı", "numeric"),
                ],
                54,
                410,
                560,
                210,
                115,
                "band_rank",
            ),
        ]

    if display_name == "Tutar ve Zaman Analizi":
        return [
            slicer_visual("amount_band_slicer", "fact_train_transactions", "amount_band", "Tutar bandı", 54, 118, 170, 72, 110),
            bar_visual(
                "amount_band_rate",
                "mart_amount_bands",
                "amount_band",
                "fraud_rate",
                "Tutar bandı",
                "Tutar bandı fraud oranı",
                54,
                214,
                340,
                170,
                111,
            ),
            line_visual(
                "daily_ma7_rate",
                "mart_daily_stats",
                "transaction_day",
                "fraud_rate_ma7",
                "Gün",
                "7 günlük fraud trendi",
                430,
                118,
                728,
                266,
                112,
            ),
            table_visual(
                "daily_drift_table",
                "mart_daily_stats",
                [
                    ("transaction_day", "Gün", "category"),
                    ("transaction_count", "İşlem", "numeric"),
                    ("fraud_rate", "Fraud oranı", "numeric"),
                    ("fraud_rate_ma7", "7g ortalama", "numeric"),
                    ("drift_flag", "Drift durumu", "category"),
                ],
                54,
                416,
                590,
                214,
                113,
                "transaction_day",
            ),
        ]

    if display_name == "Ödeme ve Email Segmentleri":
        return [
            slicer_visual("email_domain_slicer", "fact_train_transactions", "purchaser_email_group", "Email grubu", 58, 118, 190, 72, 110),
            bar_visual(
                "payment_card_network_fraud",
                "fact_train_transactions",
                "card_network",
                "is_fraud",
                "Kart ağı",
                "Kart ağı sahte işlem adedi",
                58,
                214,
                240,
                126,
                111,
            ),
            bar_visual(
                "payment_card_type_fraud",
                "fact_train_transactions",
                "card_type",
                "is_fraud",
                "Kart tipi",
                "Kart tipi sahte işlem adedi",
                324,
                214,
                234,
                126,
                112,
            ),
            bar_visual(
                "email_domain_rate",
                "mart_email_domain_stats",
                "purchaser_email_group",
                "fraud_rate",
                "Email domain",
                "Email domain fraud oranı",
                628,
                118,
                520,
                190,
                113,
                "clusteredBarChart",
            ),
            table_visual(
                "email_domain_table",
                "mart_email_domain_stats",
                [
                    ("purchaser_email_group", "Email grubu", "category"),
                    ("transaction_count", "İşlem", "numeric"),
                    ("fraud_rate", "Fraud oranı", "numeric"),
                    ("lift", "Lift", "numeric"),
                    ("fraud_share", "Fraud payı", "numeric"),
                ],
                628,
                330,
                520,
                176,
                114,
                "purchaser_email_group",
            ),
        ]

    if display_name == "Model Skorlama ve Risk Bantları":
        return [
            slicer_visual("model_risk_slicer", "fact_train_transactions", "risk_band", "Risk bandı", 58, 118, 160, 72, 110),
            bar_visual(
                "model_observed_rate",
                "mart_risk_band_stats",
                "risk_band",
                "observed_fraud_rate",
                "Risk bandı",
                "Risk bandı gözlenen fraud oranı",
                58,
                214,
                330,
                166,
                111,
            ),
            bar_visual(
                "model_capture_rate",
                "mart_risk_band_stats",
                "risk_band",
                "expected_fraud_capture",
                "Risk bandı",
                "Risk bandı yakalama payı",
                424,
                118,
                330,
                262,
                112,
            ),
            table_visual(
                "model_review_queue",
                "mart_risk_band_stats",
                [
                    ("risk_band", "Risk bandı", "category"),
                    ("review_priority", "Öncelik", "category"),
                    ("transaction_count", "İşlem", "numeric"),
                    ("observed_fraud_rate", "Fraud oranı", "numeric"),
                    ("expected_fraud_capture", "Yakalama payı", "numeric"),
                ],
                790,
                118,
                360,
                262,
                113,
                "band_rank",
            ),
        ]

    if display_name == "Veri Kalitesi ve Mimari":
        return [
            table_visual(
                "quality_missingness_table",
                "mart_feature_missingness",
                [
                    ("column_family", "Feature ailesi", "category"),
                    ("column_name", "Kolon", "category"),
                    ("missing_rate", "Eksiklik oranı", "numeric"),
                    ("missing_count", "Eksik kayıt", "numeric"),
                ],
                62,
                326,
                550,
                298,
                110,
                "column_family",
            ),
            bar_visual(
                "quality_missingness_bar",
                "mart_feature_missingness",
                "column_family",
                "missing_rate",
                "Feature ailesi",
                "Feature ailesi eksiklik skoru",
                654,
                318,
                500,
                190,
                111,
                "clusteredBarChart",
            ),
            card_visual("quality_row_count", "mart_feature_missingness", "row_count", "Profil edilen satır", 654, 526, 230, 86, 112),
            card_visual("quality_missing_count", "mart_feature_missingness", "missing_count", "Eksik değer sinyali", 922, 526, 230, 86, 113),
        ]

    return []


def add_native_analytics_page(layout: dict) -> dict:
    section = {
        "config": "{}",
        "displayName": "Canlı Analitik Katmanı",
        "displayOption": 1,
        "filters": "[]",
        "height": 720,
        "name": f"ReportSection{len(layout['sections'])}",
        "ordinal": len(layout["sections"]),
        "width": 1280,
        "visualContainers": [
            textbox_visual(
                "native_title",
                "Canlı Analitik Katmanı: DirectQuery model alanlarıyla çalışan doğrulama sayfası",
                44,
                28,
                1120,
                48,
                1000,
                20,
                True,
            ),
            textbox_visual(
                "native_subtitle",
                "Bu sayfadaki görseller Power BI modelindeki mart tablolarına bağlıdır; statik anlatım sayfalarının veri modeline bağlandığını kontrol etmek için kullanılır.",
                46,
                76,
                1120,
                40,
                1001,
                12,
            ),
            card_visual("native_total_txn", "mart_fraud_summary", "total_transactions", "Toplam işlem", 54, 128, 250, 88, 1),
            card_visual("native_fraud_txn", "mart_fraud_summary", "fraud_transactions", "Sahte işlem", 326, 128, 250, 88, 2),
            card_visual("native_fraud_rate", "mart_fraud_summary", "fraud_rate", "Baz sahtecilik oranı", 598, 128, 250, 88, 3),
            card_visual("native_identity_rate", "mart_fraud_summary", "identity_coverage_rate", "Identity kapsama", 870, 128, 250, 88, 4),
            bar_visual(
                "native_amount_band_risk",
                "mart_amount_bands",
                "amount_band",
                "fraud_rate",
                "Tutar bandı",
                "Tutar bandı sahtecilik oranı",
                54,
                246,
                360,
                190,
                5,
            ),
            line_visual(
                "native_daily_fraud_rate",
                "mart_daily_stats",
                "transaction_day",
                "fraud_rate_ma7",
                "Gün",
                "7 günlük sahtecilik oranı",
                452,
                246,
                380,
                190,
                6,
            ),
            bar_visual(
                "native_email_domain_risk",
                "mart_email_domain_stats",
                "purchaser_email_group",
                "fraud_rate",
                "Email domain",
                "Email domain sahtecilik oranı",
                868,
                246,
                330,
                190,
                7,
                "clusteredBarChart",
            ),
            table_visual(
                "native_risk_band_queue",
                "mart_risk_band_stats",
                [
                    ("split", "Veri kesiti", "category"),
                    ("risk_band", "Risk bandı", "category"),
                    ("review_priority", "İnceleme önceliği", "category"),
                    ("transaction_count", "İşlem adedi", "numeric"),
                    ("observed_fraud_rate", "Gözlenen sahtecilik oranı", "numeric"),
                    ("lift", "Lift", "numeric"),
                    ("expected_fraud_capture", "Yakalanan risk payı", "numeric"),
                ],
                54,
                470,
                544,
                178,
                8,
                "band_rank",
            ),
            table_visual(
                "native_quality_watch",
                "mart_feature_missingness",
                [
                    ("column_family", "Feature ailesi", "category"),
                    ("column_name", "Kolon", "category"),
                    ("missing_rate", "Eksiklik oranı", "numeric"),
                    ("missing_count", "Eksik kayıt", "numeric"),
                ],
                634,
                470,
                430,
                178,
                9,
                "column_family",
            ),
        ],
    }
    layout["sections"].append(section)
    layout["config"] = json.dumps(
        {
            **json.loads(layout["config"]),
            "activeSectionIndex": 0,
        },
        separators=(",", ":"),
    )
    return layout


def apply_enhanced_page_layouts(layout: dict) -> dict:
    for section in layout["sections"]:
        placements = PAGE_IMAGE_LAYOUTS.get(section["displayName"])
        if not placements:
            continue
        text_containers = []
        for container in section["visualContainers"]:
            config = json.loads(container.get("config", "{}"))
            if config.get("singleVisual", {}).get("visualType") == "textbox":
                text_containers.append(container)
        visuals = list(text_containers)
        for index, (asset_name, x, y, width, height) in enumerate(placements, start=20):
            visuals.append(image_visual(f"enhanced_{section['ordinal']}_{index}", asset_name, x, y, width, height, index))
        visuals.extend(main_page_native_visuals(section["displayName"]))
        section["visualContainers"] = visuals
    return layout


def update_registered_resource_manifest(layout: dict, resources: dict[str, bytes]) -> dict:
    resource_packages = layout.setdefault("resourcePackages", [])
    registered_package = None
    for package in resource_packages:
        resource_package = package.get("resourcePackage", {})
        if resource_package.get("name") == "RegisteredResources":
            registered_package = resource_package
            break

    if registered_package is None:
        registered_package = {
            "disabled": False,
            "items": [],
            "name": "RegisteredResources",
            "type": 1,
        }
        resource_packages.append({"resourcePackage": registered_package})

    items = registered_package.setdefault("items", [])
    known = {item.get("name") for item in items}
    for path in sorted(resources):
        if not path.startswith("Report/StaticResources/RegisteredResources/") or not path.endswith(".png"):
            continue
        asset_name = Path(path).name
        if asset_name not in known:
            items.append({"name": asset_name, "path": asset_name, "type": 100})
            known.add(asset_name)
    return layout


def add_png_content_type(raw: bytes) -> bytes:
    namespace = "http://schemas.openxmlformats.org/package/2006/content-types"
    ET.register_namespace("", namespace)
    root = ET.fromstring(raw.decode("utf-8-sig"))

    for child in list(root):
        if child.attrib.get("PartName") == "/SecurityBindings":
            root.remove(child)

    has_png = any(child.attrib.get("Extension") == "png" for child in root)
    if not has_png:
        png = ET.Element(f"{{{namespace}}}Default", {"Extension": "png", "ContentType": ""})
        root.insert(0, png)

    return ("\ufeff" + ET.tostring(root, encoding="unicode")).encode("utf-8")


def copy_assets(resources: dict[str, bytes]) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in resources.items():
        if name.startswith("Report/StaticResources/RegisteredResources/") and name.endswith(".png"):
            (ASSET_DIR / Path(name).name).write_bytes(data)


def collect_local_assets() -> dict[str, bytes]:
    resources: dict[str, bytes] = {}
    if not ASSET_DIR.exists():
        return resources
    for path in ASSET_DIR.glob("*.png"):
        resources[f"Report/StaticResources/RegisteredResources/{path.name}"] = path.read_bytes()
    return resources


def build_pbix() -> None:
    if not BASE_PBIX.exists():
        raise FileNotFoundError(f"Base PBIX not found: {BASE_PBIX}")

    POWERBI_DIR.mkdir(parents=True, exist_ok=True)
    layout, resources = read_layout_template()
    resources.update(collect_local_assets())
    layout = normalize_layout(layout)
    layout = update_registered_resource_manifest(layout, resources)
    layout = apply_enhanced_page_layouts(layout)
    layout = add_native_analytics_page(layout)
    layout_bytes = json.dumps(layout, ensure_ascii=False, separators=(",", ":")).encode("utf-16le")

    with ZipFile(BASE_PBIX, "r") as source:
        entries = {name: source.read(name) for name in source.namelist()}

    entries.pop("SecurityBindings", None)
    entries["Report/Layout"] = layout_bytes
    for name, data in resources.items():
        entries[name] = data
    entries["[Content_Types].xml"] = add_png_content_type(entries["[Content_Types].xml"])

    tmp = FINAL_PBIX.with_suffix(".pbix.tmp")
    with ZipFile(tmp, "w", compression=ZIP_DEFLATED) as target:
        for name, data in entries.items():
            target.writestr(name, data)
    shutil.move(str(tmp), str(FINAL_PBIX))
    copy_assets(resources)
    print(f"Power BI v2 report ready: {FINAL_PBIX}")


if __name__ == "__main__":
    build_pbix()
