from __future__ import annotations

import importlib
import json
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


def text_from_codes(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


def test_dashboard_table_contract_is_allowlisted() -> None:
    assert set(main.TABLE_QUERIES) == set(main.BIGQUERY_TABLES)
    assert "fraud_transactions" not in set(main.BIGQUERY_TABLES.values())
    assert "rpt_executive_kpis" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_segment_watchlist" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_identity_product_coverage" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_time_amount_signals" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_report_narrative" in set(main.BIGQUERY_TABLES.values())
    assert main.BIGQUERY_TABLES["niche_drilldown"] == "fact_train_transactions"


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


def test_public_api_normalizer_keeps_reporting_copy_business_ready() -> None:
    row = main.normalize_public_row(
        "segment_watchlist",
        {
            "segment_family": "Amount band",
            "segment_name": "01. <$25",
            "risk_priority": "Critical",
            "recommended_action": "Legacy action",
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


def test_metadata_endpoint_contract_is_business_ready() -> None:
    payload = main.metadata()
    payload_text = json.dumps(payload, ensure_ascii=False)

    assert payload["presentation_layer"] == "web_dashboard"
    assert payload["dataset"] == "fraud_project_reporting"
    assert payload["table_count"] == 19
    assert len(payload["kpi_definitions"]) >= 8
    assert len(payload["methodology_notes"]) >= 5
    assert len(payload["executive_takeaways"]) >= 3
    assert len(payload["data_dictionary"]) >= 10
    assert len(payload["model_reproducibility"]) >= 3
    assert len(payload["threshold_decision_policy"]) >= 4
    assert len(payload["business_impact_scenarios"]) >= 4
    assert len(payload["model_governance_controls"]) >= 4
    assert len(payload["monitoring_playbook"]) >= 4
    assert len(payload["production_validation"]) >= 5
    assert len(payload["page_action_messages"]) == 4
    assert any(item["kpi"] == "Fraud rate" for item in payload["kpi_definitions"])
    assert any(item["kpi"] == "Review workload" for item in payload["kpi_definitions"])
    assert any(item["metric"] == "Brier score" for item in payload["model_validation_metrics"])
    assert any(item["metric"] == "Expected calibration error" for item in payload["model_validation_metrics"])
    assert any(item["rule"] == "Primary operating rule" for item in payload["threshold_decision_policy"])
    assert any(item["field"] == "TransactionDT" for item in payload["data_dictionary"])
    assert any("TransactionDT" in item["note"] for item in payload["methodology_notes"])
    assert any("automated decline" in item["note"] for item in payload["methodology_notes"])
    assert "web_dashboard" in payload_text
    assert "Power" + " BI" not in payload_text
    assert "p" + "bix" not in payload_text.lower()
    assert "\u00c3" not in payload_text
    assert "\u00c4" not in payload_text


def test_web_dashboard_contains_interactive_analysis_controls() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

    assert '<html lang="en">' in html
    assert "Executive Overview" in html
    assert "Segment Explorer" in html
    assert "Model Operations" in html
    assert "Data Trust" in html
    assert "01 Executive Overview" not in html
    assert "02 Segment Explorer" not in html
    assert "03 Model Operations" not in html
    assert "04 Data Trust" not in html
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
    assert "compare-family-select" in html
    assert "comparison-panel" in html
    assert "niche-drilldown" in html
    assert "decision-story" in html
    assert "family-concentration-bars" in html
    assert "analyst-capacity" in html
    assert "fp-cost" in html
    assert "fn-loss" in html
    assert "alert-list" in html
    assert "waterfall-chart" in html
    assert "action-register" in html
    assert "portfolio-exposure" in html
    assert "model-validation-scorecard" in html
    assert "threshold-confusion-matrix" in html
    assert "analysis-coverage-matrix" in html
    assert "hypothesis-register" in html
    assert "executive-takeaways" in html
    assert "segment-action-playbook" in html
    assert "operating-point-recommendation" in html
    assert "business-impact-sensitivity" in html
    assert "calibration-analysis" in html
    assert "overview-action-banner" in html
    assert "segment-action-banner" in html
    assert "model-action-banner" in html
    assert "quality-action-banner" in html
    assert "segment-interaction-insights" in html
    assert "threshold-decision-policy" in html
    assert "monitoring-playbook" in html
    assert "model-governance-controls" in html
    assert "production-validation-gate" in html
    assert "feature-family-explainability" in html
    assert "data-dictionary" in html
    assert "model-reproducibility" in html
    assert "download-memo-btn" in html
    assert "kpi-dictionary" in html
    assert "methodology-notes" in html
    assert "/api/metadata" in html
    assert "export-json-btn" in html
    assert "print-btn" in html
    assert "copy-summary-btn" in html
    assert "selectedThresholdScenario" in html
    assert "Selected threshold" in html
    assert "Move the slider to compare scenarios" in html
    assert "chart focus" in html
    assert "Fraud amount exposure" in html
    assert "Selected-threshold confusion matrix" in html
    assert "Analysis coverage matrix" in html


def test_threshold_slider_updates_selected_scenario_cards() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    section = html.split("function renderThresholdRecommendation()", 1)[1].split(
        "function renderReviewTable()",
        1,
    )[0]

    assert "selectedThresholdScenario()" in section
    assert "thresholdRecommendation()" not in section
    assert "Capture / precision" in section


def test_metadata_contains_full_analysis_coverage() -> None:
    payload = main.metadata()

    assert len(payload["analysis_coverage"]) >= 12
    assert len(payload["hypothesis_register"]) >= 5
    assert len(payload["model_validation_metrics"]) >= 5
    assert any(item["metric"] == "KS statistic" for item in payload["model_validation_metrics"])
    assert any(item["metric"] == "p95 precision" for item in payload["model_validation_metrics"])
    assert len(payload["executive_takeaways"]) >= 3
    assert len(payload["data_dictionary"]) >= 10
    assert len(payload["model_reproducibility"]) >= 3
    assert any(item["area"] == "Business impact" for item in payload["analysis_coverage"])
    assert any(item["area"] == "ML performance" for item in payload["analysis_coverage"])
    assert any(item["metric"] == "ROC-AUC" for item in payload["model_validation_metrics"])


def test_web_dashboard_public_ui_is_english_only() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    blocked_patterns = [
        "tr-TR",
        text_from_codes(89, 111, 110, 101, 116, 105, 99, 105),
        text_from_codes(89, 246, 110, 101, 116, 105, 99, 105),
        text_from_codes(79, 122, 101, 116),
        text_from_codes(214, 122, 101, 116),
        text_from_codes(84, 117, 116, 97, 114),
        text_from_codes(79, 100, 101, 109, 101),
        text_from_codes(214, 100, 101, 109, 101),
        text_from_codes(86, 101, 114, 105, 32, 75, 97, 108, 105, 116, 101, 115, 105),
        text_from_codes(84, 117, 114, 107),
        text_from_codes(84, 252, 114, 107),
        blocked_text("P", "ower", " ", "B", "I"),
        blocked_text("p", "ower", "b", "i"),
        blocked_text("p", "b", "i", "x"),
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
        text_from_codes(89, 111, 110, 101, 116, 105, 99, 105),
        text_from_codes(89, 246, 110, 101, 116, 105, 99, 105),
        text_from_codes(79, 122, 101, 116),
        text_from_codes(214, 122, 101, 116),
        text_from_codes(84, 117, 116, 97, 114),
        text_from_codes(79, 100, 101, 109, 101),
        text_from_codes(214, 100, 101, 109, 101),
        text_from_codes(86, 101, 114, 105, 32, 75, 97, 108, 105, 116, 101, 115, 105),
        text_from_codes(75, 114, 105, 116, 105, 107),
        text_from_codes(89, 117, 107, 115, 101, 107),
        text_from_codes(89, 252, 107, 115, 101, 107),
        text_from_codes(65, 99, 105, 108),
        text_from_codes(71, 252, 110, 108, 252, 107),
        text_from_codes(72, 97, 102, 116, 97, 108, 305, 107),
        text_from_codes(83, 97, 104, 116, 101),
        blocked_text("P", "ower", " ", "B", "I"),
        blocked_text("p", "ower", "b", "i"),
        blocked_text("p", "b", "i", "x"),
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
