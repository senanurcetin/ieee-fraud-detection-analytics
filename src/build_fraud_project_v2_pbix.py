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
        ("17_executive_control_panel.png", 44, 124, 1138, 168),
        ("10_product_lift.png", 52, 316, 352, 198),
        ("11_identity_lift.png", 464, 316, 352, 198),
        ("24_risk_funnel.png", 876, 316, 352, 198),
        ("21_executive_decision_matrix.png", 138, 532, 1004, 150),
    ],
    "Risk Konsantrasyonu": [
        ("18_segment_watchlist.png", 54, 126, 1110, 300),
        ("10_product_lift.png", 58, 462, 360, 205),
        ("11_identity_lift.png", 460, 462, 360, 205),
        ("04_product_device_risk.png", 862, 462, 330, 205),
    ],
    "Tutar ve Zaman Analizi": [
        ("03_amount_bands.png", 58, 132, 520, 250),
        ("14_amount_distribution.png", 650, 132, 500, 250),
        ("02_daily_fraud_rate.png", 58, 414, 560, 230),
        ("15_hourly_pattern.png", 676, 414, 470, 230),
    ],
    "Ödeme ve Email Segmentleri": [
        ("12_card_payment_heatmap.png", 72, 130, 500, 390),
        ("13_email_domain_risk.png", 650, 130, 500, 390),
        ("21_executive_decision_matrix.png", 134, 540, 1010, 130),
    ],
    "Model Skorlama ve Risk Bantları": [
        ("19_model_threshold_simulation.png", 60, 128, 680, 260),
        ("22_review_strategy_matrix.png", 780, 128, 390, 260),
        ("05_feature_importance.png", 58, 414, 520, 245),
        ("08_risk_bands.png", 650, 414, 500, 245),
    ],
    "Veri Kalitesi ve Mimari": [
        ("25_dbt_quality_gate.png", 70, 130, 1060, 210),
        ("07_missingness_by_family.png", 78, 362, 520, 300),
        ("09_architecture.png", 646, 372, 500, 270),
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
