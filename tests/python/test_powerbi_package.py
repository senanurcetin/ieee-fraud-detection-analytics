from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PBIX = ROOT / "powerbi" / "fraud_project_v2.pbix"
DAX_FILE = ROOT / "powerbi" / "dax" / "fraud_project_measures.dax"


def test_powerbi_report_has_six_pages_and_no_embedded_images() -> None:
    assert PBIX.exists(), "Power BI report is missing"

    with zipfile.ZipFile(PBIX) as zf:
        assert zf.testzip() is None
        names = zf.namelist()
        layout = json.loads(zf.read("Report/Layout").decode("utf-16le"))

    assert len(layout["sections"]) == 6
    assert "SecurityBindings" not in names
    assert not [
        name
        for name in names
        if name.startswith("Report/StaticResources/RegisteredResources/") and name.lower().endswith(".png")
    ]


def test_dax_measure_catalog_is_present() -> None:
    assert DAX_FILE.exists(), "DAX measure catalog is missing"
    text = DAX_FILE.read_text(encoding="utf-8")

    measures = [line for line in text.splitlines() if line.strip().endswith("=")]
    assert len(measures) >= 20
    assert "Segment Fraud Lift =" in text
    assert "Yönetici Karar Mesajı =" in text
