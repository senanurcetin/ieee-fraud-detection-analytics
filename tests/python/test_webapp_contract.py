from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from webapp import main


def test_dashboard_table_contract_is_allowlisted() -> None:
    assert set(main.TABLE_QUERIES) == set(main.BIGQUERY_TABLES)
    assert "fraud_transactions" not in set(main.BIGQUERY_TABLES.values())
    assert "rpt_executive_kpis" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_segment_watchlist" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_identity_product_coverage" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_time_amount_signals" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_report_narrative" in set(main.BIGQUERY_TABLES.values())


def test_qualified_table_rejects_unexpected_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "portfolio-project")
    monkeypatch.setenv("BQ_DATASET", "fraud_project_reporting")

    assert main.qualified_table("rpt_executive_kpis") == "`portfolio-project.fraud_project_reporting.rpt_executive_kpis`"

    with pytest.raises(ValueError):
        main.qualified_table("raw_train_transaction")


def test_to_jsonable_converts_bigquery_scalar_types() -> None:
    assert main.to_jsonable(Decimal("3.14")) == 3.14
    assert main.to_jsonable(date(2026, 5, 25)) == "2026-05-25"
    assert main.to_jsonable("Critical") == "Critical"


def test_web_dashboard_contains_interactive_analysis_controls() -> None:
    html = (Path(__file__).resolve().parents[2] / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

    assert '<html lang="en">' in html
    assert "Executive Overview" in html
    assert "Segment Explorer" in html
    assert "Model Operations" in html
    assert "Data Trust" in html
    assert "metric-select" in html
    assert "family-select" in html
    assert "priority-select" in html
    assert "drill-drawer" in html
    assert "threshold-slider" in html
    assert "pareto-chart" in html
    assert "driver-tree" in html
    assert "feature-treemap" in html
    assert "compare-a-select" in html
    assert "compare-b-select" in html
    assert "comparison-panel" in html
    assert "analyst-capacity" in html
    assert "fp-cost" in html
    assert "fn-loss" in html
    assert "alert-list" in html
    assert "waterfall-chart" in html
    assert "export-json-btn" in html
    assert "print-btn" in html
    assert "copy-summary-btn" in html


def test_web_dashboard_public_ui_is_english_only() -> None:
    html = (Path(__file__).resolve().parents[2] / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    blocked_patterns = [
        "tr-TR",
        "Yonetici",
        "Y\u00f6netici",
        "Ozet",
        "\u00d6zet",
        "Tutar",
        "Odeme",
        "\u00d6deme",
        "Veri Kalitesi",
        "Turk",
        "T\u00fcrk",
        "Power BI",
        "powerbi",
        "pbix",
        "\u00c3",
        "\u00c4",
        "\u00c5",
        "\u00c2",
    ]
    for pattern in blocked_patterns:
        assert pattern not in html
