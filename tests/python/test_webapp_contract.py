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
    assert "pbi_executive_kpis" in set(main.BIGQUERY_TABLES.values())
    assert "pbi_segment_watchlist" in set(main.BIGQUERY_TABLES.values())
    assert "pbi_identity_product_coverage" in set(main.BIGQUERY_TABLES.values())
    assert "pbi_time_amount_signals" in set(main.BIGQUERY_TABLES.values())
    assert "pbi_report_narrative" in set(main.BIGQUERY_TABLES.values())


def test_qualified_table_rejects_unexpected_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "portfolio-project")
    monkeypatch.setenv("BQ_DATASET", "fraud_project_powerbi")

    assert main.qualified_table("pbi_executive_kpis") == "`portfolio-project.fraud_project_powerbi.pbi_executive_kpis`"

    with pytest.raises(ValueError):
        main.qualified_table("raw_train_transaction")


def test_to_jsonable_converts_bigquery_scalar_types() -> None:
    assert main.to_jsonable(Decimal("3.14")) == 3.14
    assert main.to_jsonable(date(2026, 5, 25)) == "2026-05-25"
    assert main.to_jsonable("Critical") == "Critical"


def test_web_dashboard_contains_interactive_analysis_controls() -> None:
    html = (Path(__file__).resolve().parents[2] / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

    assert "metric-select" in html
    assert "family-select" in html
    assert "priority-select" in html
    assert "drill-drawer" in html
    assert "threshold-slider" in html
    assert "pareto-chart" in html
    assert "driver-tree" in html
    assert "feature-treemap" in html
