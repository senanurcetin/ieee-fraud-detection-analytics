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


def test_enterprise_metadata_contract_is_explicit_about_dataset_limits() -> None:
    payload = main.enterprise_metadata()

    assert payload["presentation_layer"] == "web_dashboard"
    assert "Executive Fraud Overview" in payload["enterprise_pages"]
    assert "Fraud Trend Analysis" in payload["enterprise_pages"]
    assert "Transaction Amount Analysis" in payload["enterprise_pages"]
    assert "Customer Risk Analysis" in payload["enterprise_pages"]
    assert "Masked Address & Distance Analysis" in payload["enterprise_pages"]
    assert "Behavioral Pattern Analysis" in payload["enterprise_pages"]
    assert "Feature Importance Analysis" in payload["enterprise_pages"]
    assert "Model Performance Analysis" in payload["enterprise_pages"]
    assert "Key Insights & Recommendations" in payload["enterprise_pages"]
    assert "Alert Management" not in payload["enterprise_pages"]
    assert "country" in payload["unsupported_fields"]
    assert "user_age" in payload["unsupported_fields"]


def test_enterprise_case_helpers_create_operational_risk_contract() -> None:
    assert main.risk_category_from_band("Critical") == "Critical"
    assert main.risk_category_from_band("High") == "High Risk"
    assert main.risk_category_from_band("Elevated") == "Medium Risk"
    assert main.risk_category_from_band("Low") == "Low Risk"
    assert main.recommended_action_from_band("Critical") == "Immediate manual review"

    explanation = main.build_transaction_explanation(
        {
            "risk_band": "Critical",
            "model_probability": 0.42,
            "transaction_amount": 600,
            "identity_status": "Identity present",
            "purchaser_email_group": "anonymous.com",
        },
    )

    assert len(explanation) >= 4
    assert any(item["factor"] == "Model risk band" for item in explanation)
    assert any(item["factor"] == "High ticket size" for item in explanation)


def test_enterprise_case_sql_omits_unsupported_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "portfolio-project")
    monkeypatch.setenv("BQ_DATASET", "fraud_project_reporting")

    sql = main.case_queue_sql(limit=20).lower()

    assert "risk_score" in sql
    assert "risk_category" in sql
    assert "entity_prior_fraud_proxy" in sql
    assert "model_confidence" in sql
    assert "country" not in sql
    assert "user_age" not in sql


def test_web_dashboard_contains_interactive_analysis_controls() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

    assert '<html lang="en">' in html
    assert "Executive Fraud Overview" in html
    assert "Fraud Trend Analysis" in html
    assert "Transaction Amount Analysis" in html
    assert "Customer Risk Analysis" in html
    assert "Masked Address & Distance Analysis" in html
    assert "Behavioral Pattern Analysis" in html
    assert "Feature Importance Analysis" in html
    assert "Model Performance Analysis" in html
    assert "Key Insights & Recommendations" in html
    assert "Analyst Investigation Queue" not in html
    assert "Alert Management" not in html
    assert "SOC" not in html
    assert "ticketing" not in html
    assert 'data-view="quality"' not in html
    assert "01 Executive Overview" not in html
    assert "02 Segment Explorer" not in html
    assert "03 Model Operations" not in html
    assert "04 Data Trust" not in html
    assert "day-filter" in html
    assert "product-filter" in html
    assert "amount-filter" in html
    assert "email-filter" in html
    assert "identity-filter" in html
    assert "risk-filter" in html
    assert "clear-btn" in html
    assert "theme-btn" in html
    assert "csv-btn" in html
    assert "pdf-btn" in html
    assert "threshold-select" in html
    assert "threshold-slider" in html
    assert "detail-drawer" in html
    assert "metricLayer()" in html
    assert "overview-trend" in html
    assert "overview-donut" in html
    assert "overview-product" in html
    assert "overview-pareto" in html
    assert "trend-line" in html
    assert "trend-combo" in html
    assert "trend-hour" in html
    assert "amount-bar" in html
    assert "amount-heatmap" in html
    assert "amount-scatter" in html
    assert "amount-boxplot" in html
    assert "customer-identity" in html
    assert "customer-email" in html
    assert "customer-device" in html
    assert "customer-matrix" in html
    assert "proxy-missingness" in html
    assert "proxy-importance" in html
    assert "proxy-entity" in html
    assert "proxy-heatmap" in html
    assert "behavior-hour" in html
    assert "behavior-payment-email" in html
    assert "feature-bar" in html
    assert "feature-family" in html
    assert "feature-scatter" in html
    assert "model-threshold" in html
    assert "model-curves" in html
    assert "model-risk" in html
    assert "model-confusion" in html
    assert "insight-matrix" in html
    assert "insight-waterfall" in html
    assert "/api/dashboard" in html
    assert "/api/metadata" in html
    assert "/api/enterprise/cases?limit=240" in html
    assert "Selected threshold" in html
    assert "Fraud Exposure" in html
    assert "Capturable Exposure" in html
    assert "Native Location Fields" in html
    assert "Drill Path" in html


def test_threshold_slider_updates_selected_scenario_cards() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    section = html.split("function renderThresholdSummary()", 1)[1].split(
        "function confusionMatrix",
        1,
    )[0]

    assert "selectedThreshold()" in section
    assert "Fraud Capture" in section
    assert "Missed Exposure" in section
    assert "Precision" in section
    assert "Workload" in section


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
