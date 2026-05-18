from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


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


def add_png_content_type(raw: bytes) -> bytes:
    text = raw.decode("utf-8-sig")
    if 'Extension="png"' not in text:
        text = text.replace(
            '<Default Extension="json" ContentType="" />',
            '<Default Extension="png" ContentType="" /><Default Extension="json" ContentType="" />',
            1,
        )
    return ("\ufeff" + text.lstrip("\ufeff")).encode("utf-8")


def copy_assets(resources: dict[str, bytes]) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in resources.items():
        if name.startswith("Report/StaticResources/RegisteredResources/") and name.endswith(".png"):
            (ASSET_DIR / Path(name).name).write_bytes(data)


def build_pbix() -> None:
    if not BASE_PBIX.exists():
        raise FileNotFoundError(f"Base PBIX not found: {BASE_PBIX}")

    POWERBI_DIR.mkdir(parents=True, exist_ok=True)
    layout, resources = read_layout_template()
    layout = normalize_layout(layout)
    layout_bytes = json.dumps(layout, ensure_ascii=False, separators=(",", ":")).encode("utf-16le")

    with ZipFile(BASE_PBIX, "r") as source:
        entries = {name: source.read(name) for name in source.namelist()}

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
