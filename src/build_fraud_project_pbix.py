from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
BASE_PBIX = ROOT / "outputs" / "powerbi" / "fraud_project.pbix"
LAYOUT_TEMPLATE = ROOT / "outputs" / "powerbi" / "fraud_project_dashboard.pbit"
POWERBI_DIR = ROOT / "powerbi"
ASSET_DIR = POWERBI_DIR / "assets"
FINAL_PBIX = POWERBI_DIR / "fraud_project.pbix"

PAGE_ORDER = [
    ("Yonetici Ozeti", "Yönetici Özeti"),
    ("Urun Identity", "Risk Konsantrasyonu"),
    ("Tutar Zaman", "Tutar ve Zaman Analizi"),
    ("Odeme Email", "Ödeme ve Email Segmentleri"),
    ("Model Riski", "Model Skorlama ve Risk Bantları"),
    ("Veri Kalitesi", "Veri Kalitesi ve Mimari"),
]


def read_layout_from_template() -> tuple[dict, dict[str, bytes]]:
    if not LAYOUT_TEMPLATE.exists():
        raise FileNotFoundError(f"Layout template not found: {LAYOUT_TEMPLATE}")

    resources: dict[str, bytes] = {}
    with ZipFile(LAYOUT_TEMPLATE, "r") as zf:
        layout = json.loads(zf.read("Report/Layout").decode("utf-16le"))
        for name in zf.namelist():
            if name.startswith("Report/StaticResources/"):
                resources[name] = zf.read(name)
    return layout, resources


def update_page_order(layout: dict) -> dict:
    source_sections = {section["displayName"]: section for section in layout["sections"]}
    sections = []
    for ordinal, (old_name, new_name) in enumerate(PAGE_ORDER):
        section = source_sections[old_name]
        section["displayName"] = new_name
        section["ordinal"] = ordinal
        section["name"] = f"ReportSection{ordinal}"
        sections.append(section)
    layout["sections"] = sections
    return layout


def content_types_with_png(raw: bytes) -> bytes:
    text = raw.decode("utf-8-sig")
    if 'Extension="png"' not in text:
        text = text.replace(
            "<Types ",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types" ',
            1,
        ) if "xmlns=" not in text.split(">", 1)[0] else text
        text = text.replace(
            "<Default Extension=\"json\" ContentType=\"\" />",
            "<Default Extension=\"png\" ContentType=\"\" /><Default Extension=\"json\" ContentType=\"\" />",
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
    layout, resources = read_layout_from_template()
    layout = update_page_order(layout)
    layout_bytes = json.dumps(layout, ensure_ascii=False, separators=(",", ":")).encode("utf-16le")

    with ZipFile(BASE_PBIX, "r") as source:
        base_entries = {name: source.read(name) for name in source.namelist()}

    base_entries["Report/Layout"] = layout_bytes
    for name, data in resources.items():
        base_entries[name] = data
    if "[Content_Types].xml" in base_entries:
        base_entries["[Content_Types].xml"] = content_types_with_png(base_entries["[Content_Types].xml"])

    tmp = FINAL_PBIX.with_suffix(".pbix.tmp")
    with ZipFile(tmp, "w", compression=ZIP_DEFLATED) as target:
        for name, data in base_entries.items():
            target.writestr(name, data)
    shutil.move(str(tmp), str(FINAL_PBIX))
    copy_assets(resources)

    print(f"Power BI report ready: {FINAL_PBIX}")
    print(f"Power BI assets ready: {ASSET_DIR}")


if __name__ == "__main__":
    build_pbix()
