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
    assert "rpt_proxy_signal_risk" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_validation_threshold_simulation" in set(main.BIGQUERY_TABLES.values())
    assert "rpt_segment_model_performance" in set(main.BIGQUERY_TABLES.values())
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
    assert row["recommended_action"] == "Amount band requires immediate analytical focus, rule calibration, and capacity scenario review."

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
    # 27 since rpt_validation_risk_bands and rpt_model_calibration joined the layer.
    assert payload["table_count"] == 27
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
    assert len(payload["page_action_messages"]) == 9
    assert payload["model_registry"]["model_version"] == "lightgbm-v2-v339-missingness-filtered"
    assert payload["model_registry"]["feature_scope"]["v_feature_range"] == "V1-V339"
    assert any(item["kpi"] == "Fraud rate" for item in payload["kpi_definitions"])
    assert any(item["kpi"] == "Flagged workload" for item in payload["kpi_definitions"])
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


def test_enterprise_transaction_helpers_create_analytical_risk_contract() -> None:
    assert main.risk_category_from_band("Critical") == "Critical"
    assert main.risk_category_from_band("High") == "High Risk"
    assert main.risk_category_from_band("Elevated") == "Medium Risk"
    assert main.risk_category_from_band("Low") == "Low Risk"
    assert main.recommended_action_from_band("Critical") == "Immediate threshold-policy focus"

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

    registry = main.enterprise_model_registry()
    assert registry["model_version"] == "lightgbm-v2-v339-missingness-filtered"
    assert registry["feature_scope"]["v_features_selected"] == 339
    assert registry["rolling_cv_summary"]["window_count"] == 3

    importance_explanation = main.build_feature_importance_explanation(
        {
            "transaction_amount": 600,
            "transaction_day": 10,
            "transaction_hour": 4,
            "product_cd": "C",
            "identity_status": "Identity present",
            "device_type": "mobile",
            "purchaser_email_group": "gmail.com",
        },
        [
            {"feature": "TransactionAmt", "feature_family": "Core transaction", "importance": 1408, "importance_rank": 5},
            {"feature": "addr1", "feature_family": "Address", "importance": 1566, "importance_rank": 3},
            {"feature": "V87", "feature_family": "Vesta engineered V", "importance": 200, "importance_rank": 20},
        ],
    )
    assert len(importance_explanation) == 3
    assert "Transaction amount" in importance_explanation[0]["case_context"]
    assert "not a real geography" in importance_explanation[1]["case_context"]


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
    assert "overview-riskband" in html
    assert "overview-product" in html
    assert "overview-pareto" in html
    assert "trend-combo" in html
    assert "trend-drift" in html
    assert "amount-bar" in html
    assert "amount-exposure" in html
    assert "amount-heatmap" in html
    assert "amount-scatter" in html
    assert "amount-boxplot" in html
    assert "customer-identity" in html
    assert "customer-email" in html
    assert "customer-device" in html
    assert "customer-payment-email" in html
    assert "customer-matrix" in html
    assert "proxy-risk" in html
    assert "proxy-lift" in html
    assert "proxy-share" in html
    assert "proxy-product-matrix" in html
    assert "proxy-cross-matrix" in html
    assert "proxy-importance" in html
    assert "behavior-hour-risk" in html
    assert "behavior-hour" in html
    assert "feature-bar" in html
    assert "feature-family" in html
    assert "feature-scatter" in html
    assert "model-threshold" in html
    assert "model-curves" in html
    assert "model-risk" in html
    assert "model-confusion" in html
    assert "model-registry" in html
    assert "insight-matrix" in html
    assert "insight-waterfall" in html
    assert "/api/dashboard" in html
    assert "/api/metadata" in html
    assert "/api/enterprise/cases?limit=240" in html
    assert "/api/enterprise/model-registry" in html
    assert "Selected threshold" in html
    assert "Fraud Exposure" in html
    assert "Capturable Exposure" in html
    assert "Native Location Fields" in html
    assert "Validation threshold simulator" in html
    assert "Segment validation precision at selected threshold" in html
    assert "Segment-level holdout precision recalculated for the selected threshold." in html
    assert "Address Missing Risk" in html
    assert "Distance High Risk" in html
    assert "Segment Drill-through" in html
    assert "drill-back-btn" in html
    assert html.count("Fraud trend snapshot") == 1


def test_threshold_slider_updates_selected_scenario_cards() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    section = html.split("function renderThresholdSummary()", 1)[1].split(
        "function confusionMatrix",
        1,
    )[0]

    assert "selectedThreshold()" in section
    assert "const target = document.getElementById('threshold-summary');" in section
    assert "if (!target) return;" in section
    assert "target.innerHTML" in section
    assert "Fraud Capture" in section
    assert "Missed Exposure" in section
    assert "Precision" in section
    assert "Validation Workload" in section


def test_model_supporting_visuals_are_hydrated_after_threshold_guard() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    model_hydration = html.split("if (state.page === 'model')", 1)[1].split(
        "if (state.page === 'insights')",
        1,
    )[0]

    assert "renderThresholdSummary();" in model_hydration
    assert "barChart('model-features'" in model_hydration
    assert "modelRegistryCard('model-registry');" in model_hydration


def test_segment_model_precision_filters_to_selected_threshold() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    segment_section = html.split("function segmentModelRows()", 1)[1].split(
        "function deviceRiskRows()",
        1,
    )[0]

    assert "const threshold = num(selectedThreshold().score_threshold);" in segment_section
    assert "hasThresholdRows" in segment_section
    assert "Math.abs(num(row.score_threshold) - threshold) < .00001" in segment_section
    assert ".filter(row => num(row.validation_transactions) >= 1000)" in segment_section


def test_model_registry_uses_compact_metadata_layout() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    registry_section = html.split("function modelRegistryCard(id)", 1)[1].split(
        "function renderThresholdSummary()",
        1,
    )[0]

    assert ".registry-grid" in html
    assert "overflow-wrap: anywhere;" in html
    assert "function registryMetric(" in html
    assert "registryMetric('Model version', registry.model_version" in registry_section
    assert "true)" in registry_section


def test_behavior_peak_relative_hour_uses_charted_hour_risk_rows() -> None:
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

    behavior_section = html.split("function renderBehavior()", 1)[1].split(
        "function renderFeatures()",
        1,
    )[0]
    hydrate_section = html.split("barChart('behavior-hour-risk'", 1)[1].split(
        "heatmap('behavior-hour'",
        1,
    )[0]
    peak_label_section = html.split("function peakHourLabel()", 1)[1].split(
        "function bestLift",
        1,
    )[0]
    peak_row_section = html.split("function peakHourRow()", 1)[1].split(
        "function relativeHourLabel",
        1,
    )[0]

    assert "Highest hourly fraud-rate signal from the charted relative-hour pattern." in behavior_section
    assert "relativeHourLabel(row)" in hydrate_section
    assert "const top = peakHourRow();" in peak_label_section
    assert "return top ? relativeHourLabel(top) : '-';" in peak_label_section
    assert "return hourRiskRows()[0] || null;" in peak_row_section
    assert "getRows('time_amount_signals').slice().sort" not in peak_label_section
    assert "String(row.transaction_hour) + ':00'" not in html


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


def test_cost_assumptions_are_declared_and_priced_on_one_scale() -> None:
    """The dataset has no cost fields, so the economics must be stated, not buried.

    The earlier version hardcoded $5 per false positive and charged missed fraud
    at 0.15x while crediting caught fraud at face value, which priced the two
    sides of the same comparison differently.
    """
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    metric_layer = html.split("function metricLayer()", 1)[1].split(
        "function executiveEconomicsRows()",
        1,
    )[0]

    # One loss rate prices both the avoided and the residual side.
    assert "const lossRate = Math.max(num(state.fraudLossMultiplier), 0);" in metric_layer
    assert "const avoidedLoss = captured * lossRate;" in metric_layer
    assert "const residualLoss = missed * lossRate;" in metric_layer
    assert "const netBenefit = avoidedLoss - falsePositiveCost;" in metric_layer

    # The retired asymmetric constants must not come back.
    assert "missed * 0.15" not in metric_layer
    assert "* 5;" not in metric_layer

    # Both assumptions are reader-adjustable and carry their provenance.
    assert 'id="review-cost-input"' in html
    assert 'id="loss-rate-input"' in html
    assert "reviewCost: 5," in html
    assert "fraudLossMultiplier: 1," in html
    assert "IEEE-CIS contains no cost fields" in html
    assert "True Cost of Fraud" in html


def test_segment_rates_never_come_from_the_risk_ranked_review_queue() -> None:
    """Segment rates must come from governed marts, not from the case queue.

    The queue is ordered by risk band, so at limit=240 every row is Critical and
    fraudulent. Deriving a fraud rate from it reported 100% for every segment,
    and a two-filter selection put that 100% on the headline KPI cards.
    """
    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")

    context = html.split("function segmentMetricContext()", 1)[1].split(
        "function exactSegmentRow(",
        1,
    )[0]
    assert "filteredTransactions()" not in context
    assert "NICHE_FAMILY_BY_FILTER" in context
    assert "nicheCell(" in context
    assert "no governed cross-tab for this filter set" in context

    device = html.split("function deviceRiskRows()", 1)[1].split("}", 1)[0]
    assert "nicheSegmentRows('Device')" in device
    assert "filteredTransactions()" not in device

    # Fraud amounts are reported from the marts or not at all; the retired
    # $120-per-fraud constant fabricated exposure that was never measured.
    assert "* 120" not in html


def test_reporting_marts_carry_observed_fraud_amount() -> None:
    models = REPO_ROOT / "models"
    for path in [
        models / "reporting" / "rpt_product_risk.sql",
        models / "reporting" / "rpt_identity_risk.sql",
        models / "marts" / "mart_email_domain_stats.sql",
    ]:
        sql = path.read_text(encoding="utf-8")
        assert "fraud_transaction_amount" in sql, path.name

    niche = main.NICHE_DRILLDOWN_QUERY
    assert "fraud_transaction_amount" in niche
    assert "device_segment" in niche
    assert "Device" in main.NICHE_DIMENSIONS


def test_risk_band_quality_is_reported_on_the_holdout() -> None:
    """Band quality is a generalisation claim and must not come from the fit.

    The model is fitted on the first 80% of TransactionDT and then scores every
    row, so the train split is four fifths in-sample: it reports 44.59% in the
    High band against 30.34% on transactions held out of training.
    """
    assert main.BIGQUERY_TABLES["validation_risk_bands"] == "rpt_validation_risk_bands"

    model_sql = (REPO_ROOT / "models" / "reporting" / "rpt_validation_risk_bands.sql").read_text(encoding="utf-8")
    # Cut points are recovered from the scored train split so both splits are
    # partitioned identically rather than re-quantiled.
    assert "min(case when risk_band = 'Critical'" in model_sql
    assert "source('raw', 'validation_predictions')" in model_sql

    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    band_chart = html.split("function riskBandExposureChart(id)", 1)[1].split("const w = 760", 1)[0]
    assert "validation_risk_bands" in band_chart

    assert "function generalisationGapTable(" in html
    assert "generalisationGapTable('model-generalisation');" in html
    assert "Risk band exposure (holdout)" in html


def test_calibration_is_published_rather_than_assumed() -> None:
    """The score is not a probability, and the dashboard has to say so.

    Balanced class weights buy ranking quality at the cost of calibration: on
    the holdout the mean score is 5.2x the observed fraud rate and the Brier
    score loses to a constant base-rate forecast. That is publishable evidence,
    not a footnote.
    """
    assert main.BIGQUERY_TABLES["model_calibration"] == "rpt_model_calibration"

    sql = (REPO_ROOT / "models" / "reporting" / "rpt_model_calibration.sql").read_text(encoding="utf-8")
    assert "source('raw', 'validation_predictions')" in sql
    assert "brier_score" in sql
    assert "baseline_brier_score" in sql
    assert "expected_calibration_error" in sql
    assert "ntile(10)" in sql

    html = (REPO_ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    assert "function calibrationTable(" in html
    assert "calibrationTable('model-calibration');" in html
    # The card must state the limitation, not just plot it.
    assert "The score is a rank, not a likelihood" in html
