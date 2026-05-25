from __future__ import annotations

import importlib
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

main = importlib.import_module("webapp.main")

REPO_ROOT = Path(__file__).resolve().parents[2]


def blocked_text(*parts: str) -> str:
    return "".join(parts)


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


def test_duckdb_backend_uses_reporting_schema_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_DATA_BACKEND", "duckdb")

    assert main.project_label() == "local-duckdb"
    assert main.qualified_duckdb_table("rpt_executive_kpis") == '"reporting"."rpt_executive_kpis"'

    with pytest.raises(ValueError):
        main.qualified_duckdb_table("raw_train_transaction")


def test_to_jsonable_converts_bigquery_scalar_types() -> None:
    assert main.to_jsonable(Decimal("3.14")) == 3.14
    assert main.to_jsonable(date(2026, 5, 25)) == "2026-05-25"
    assert main.to_jsonable("Critical") == "Critical"


def test_public_api_normalizer_removes_legacy_reporting_copy() -> None:
    row = main.normalize_public_row(
        "segment_watchlist",
        {
            "segment_family": blocked_text("Tu", "tar", " band", "\u00c4", "\u00b1"),
            "segment_name": "01. <$25",
            "risk_priority": blocked_text("Kri", "tik"),
            "recommended_action": blocked_text("Ac", "il", " legacy action"),
        },
    )

    assert row["segment_family"] == "Amount band"
    assert row["risk_priority"] == "Critical"
    assert row["recommended_action"] == "Amount band requires immediate review, rule calibration, and capacity allocation."

    readiness = main.normalize_public_row(
        "report_readiness",
        {"check_id": "DATA_001", "status": "PASS", "readiness_area": "legacy", "check_name": "legacy"},
    )
    assert readiness["readiness_area"] == "Data reliability"
    assert readiness["check_name"] == "Raw train transaction row count"
    assert readiness["readiness_result"] == "Ready for presentation"


def test_web_dashboard_contains_interactive_analysis_controls() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

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
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    blocked_patterns = [
        "tr-TR",
        "Yonetici",
        "Y\u00f6netici",
        "Ozet",
        "\u00d6zet",
        blocked_text("Tu", "tar"),
        "O" + "deme",
        "\u00d6deme",
        blocked_text("Ve", "ri", " Kalitesi"),
        "Turk",
        "T\u00fcrk",
        "Power" + " BI",
        "power" + "bi",
        "p" + "bix",
        "\u00c3",
        "\u00c4",
        "\u00c5",
        "\u00c2",
    ]
    for pattern in blocked_patterns:
        assert pattern not in html


def test_public_text_surfaces_are_english_and_web_only() -> None:
    public_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "webapp" / "README.md",
        *sorted((REPO_ROOT / "docs").glob("*.md")),
        *sorted((REPO_ROOT / "models" / "reporting").glob("*.sql")),
        REPO_ROOT / "models" / "marts" / "mart_daily_stats.sql",
        REPO_ROOT / "models" / "marts" / "mart_risk_band_stats.sql",
        REPO_ROOT / "models" / "sources.yml",
    ]
    blocked_patterns = [
        "Yonetici",
        "Y\u00f6netici",
        "Ozet",
        "\u00d6zet",
        blocked_text("Tu", "tar"),
        "O" + "deme",
        "\u00d6deme",
        blocked_text("Ve", "ri", " Kalitesi"),
        blocked_text("Kri", "tik"),
        "Yuk" + "sek",
        "Y\u00fcksek",
        "Ac" + "il",
        "G\u00fcnl\u00fck",
        "Haftal\u0131k",
        "Sah" + "te",
        "Power" + " BI",
        "power" + "bi",
        "p" + "bix",
        "\u00c3",
        "\u00c4",
        "\u00c5",
        "\u00c2",
    ]

    failures: list[str] = []
    for path in public_files:
        text = path.read_text(encoding="utf-8")
        for pattern in blocked_patterns:
            if pattern in text:
                failures.append(f"{path.relative_to(REPO_ROOT)} contains blocked public text: {pattern}")

    assert not failures, "\n".join(failures)
