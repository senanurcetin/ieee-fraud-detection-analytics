"""FastAPI application for the live fraud analytics web dashboard."""

from __future__ import annotations

import base64
import json
import os
import time
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery
from google.oauth2 import service_account

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

DEFAULT_DATASET = "fraud_project_reporting"
DEFAULT_CACHE_SECONDS = 600
DEFAULT_DUCKDB_PATH = "data/processed/ieee_fraud.duckdb"
DUCKDB_SCHEMA = "reporting"

TABLE_QUERIES: dict[str, str] = {
    "executive_kpis": "select * from {table} limit 1",
    "product_risk": "select * from {table} order by fraud_rate desc",
    "identity_risk": "select * from {table} order by has_identity desc",
    "identity_product_coverage": "select * from {table} order by fraud_lift desc",
    "amount_bands": "select * from {table} order by amount_band",
    "daily_drift": "select * from {table} order by transaction_day",
    "time_amount_signals": "select * from {table} order by transaction_hour, amount_decimal_group",
    "payment_heatmap": "select * from {table} order by fraud_rate desc",
    "email_domain_risk": "select * from {table} order by fraud_rate desc",
    "model_risk_bands": (
        "select * from {table} "
        "where split = 'train' "
        "order by band_rank"
    ),
    "feature_importance": (
        "select feature, feature_family, importance, importance_rank "
        "from {table} "
        "where importance_rank <= 15 "
        "order by importance_rank"
    ),
    "data_quality": (
        "select "
        "column_family, "
        "sum(column_count) as column_count, "
        "avg(avg_missing_rate) as avg_missing_rate, "
        "max(max_missing_rate) as max_missing_rate, "
        "sum(total_missing_values) as total_missing_values, "
        "max(row_count) as row_count "
        "from {table} "
        "group by column_family "
        "order by avg_missing_rate desc"
    ),
    "segment_watchlist": "select * from {table} order by watchlist_rank",
    "review_strategy": "select * from {table} order by band_rank",
    "threshold_simulation": "select * from {table} order by score_threshold",
    "report_narrative": "select * from {table} order by page_order",
    "quality_contract": "select * from {table} order by object_name",
    "report_readiness": "select * from {table} order by check_id",
}

BIGQUERY_TABLES: dict[str, str] = {
    "executive_kpis": "rpt_executive_kpis",
    "product_risk": "rpt_product_risk",
    "identity_risk": "rpt_identity_risk",
    "identity_product_coverage": "rpt_identity_product_coverage",
    "amount_bands": "rpt_amount_bands",
    "daily_drift": "rpt_daily_drift",
    "time_amount_signals": "rpt_time_amount_signals",
    "payment_heatmap": "rpt_payment_heatmap",
    "email_domain_risk": "rpt_email_domain_risk",
    "model_risk_bands": "rpt_model_risk_bands",
    "feature_importance": "rpt_feature_importance",
    "data_quality": "rpt_data_quality_scorecard",
    "segment_watchlist": "rpt_segment_watchlist",
    "review_strategy": "rpt_review_strategy",
    "threshold_simulation": "rpt_threshold_simulation",
    "report_narrative": "rpt_report_narrative",
    "quality_contract": "rpt_quality_contract",
    "report_readiness": "rpt_report_readiness",
}

KPI_DEFINITIONS: list[dict[str, str]] = [
    {
        "kpi": "Total transactions",
        "definition": "Count of profiled training transactions in the governed reporting layer.",
        "business_use": "Defines the population size behind every executive percentage.",
    },
    {
        "kpi": "Fraud transactions",
        "definition": "Transactions labeled as fraud in the IEEE-CIS training data.",
        "business_use": "Measures confirmed fraud volume used for concentration and model validation.",
    },
    {
        "kpi": "Fraud rate",
        "definition": "Fraud transactions divided by total transactions.",
        "business_use": "Baseline risk level; segment rates are compared against this benchmark.",
    },
    {
        "kpi": "Identity coverage",
        "definition": "Share of transactions that join to the identity table.",
        "business_use": "Shows how often identity attributes are available and whether coverage itself carries risk signal.",
    },
    {
        "kpi": "Lift",
        "definition": "Segment fraud rate divided by the portfolio fraud rate.",
        "business_use": "Ranks segments by risk intensity relative to the baseline.",
    },
    {
        "kpi": "Fraud share",
        "definition": "Share of all fraud labels contained in a segment.",
        "business_use": "Separates high-risk niche segments from segments that also matter operationally.",
    },
    {
        "kpi": "Review workload",
        "definition": "Transactions that would enter the analyst review queue at a selected threshold.",
        "business_use": "Connects model thresholds to operational capacity planning.",
    },
    {
        "kpi": "Fraud capture",
        "definition": "Fraud labels captured by the selected model threshold or risk band.",
        "business_use": "Estimates how much fraud the proposed queue can surface for review.",
    },
    {
        "kpi": "Precision",
        "definition": "Captured fraud cases divided by reviewed transactions.",
        "business_use": "Estimates review efficiency and false-positive burden.",
    },
]

METHODOLOGY_NOTES: list[dict[str, str]] = [
    {
        "topic": "Relative time handling",
        "note": "TransactionDT is an elapsed-second counter from an unknown reference point, not a real calendar timestamp.",
        "control": "The dashboard describes time as relative day and relative hour; no calendar claims are made.",
    },
    {
        "topic": "Identity coverage",
        "note": "The identity table covers only a subset of transactions, so missing identity is analyzed as a signal rather than treated as a data defect only.",
        "control": "Identity coverage and identity-present lift are visible in executive KPIs and segment diagnostics.",
    },
    {
        "topic": "Masked features",
        "note": "Many engineered fields are anonymized by the dataset provider, so feature interpretation is observational rather than a confirmed business definition.",
        "control": "Model explanations use feature families and importance ranking instead of unsupported semantic claims.",
    },
    {
        "topic": "Model use",
        "note": "The model is a prioritization layer for review queues, not an automated decline or customer-blocking engine.",
        "control": "Threshold simulation reports capture, precision, workload, and missed exposure before recommending action.",
    },
    {
        "topic": "Threshold governance",
        "note": "Operating thresholds should be recalibrated when fraud base rate, analyst capacity, or false-positive cost changes.",
        "control": "The dashboard exposes client-side capacity and cost inputs for scenario testing.",
    },
]

OPERATING_ASSUMPTIONS: list[dict[str, str]] = [
    {
        "assumption": "Analyst capacity",
        "default_value": "180 reviews per analyst day",
        "purpose": "Used by the model operations simulator to flag queue pressure.",
    },
    {
        "assumption": "False-positive review cost",
        "default_value": "$4 per reviewed non-fraud transaction",
        "purpose": "Used to estimate operational review cost.",
    },
    {
        "assumption": "False-negative fraud loss",
        "default_value": "$120 per missed fraud transaction",
        "purpose": "Used to approximate missed fraud exposure for threshold scenarios.",
    },
    {
        "assumption": "API cache",
        "default_value": f"{DEFAULT_CACHE_SECONDS} seconds",
        "purpose": "Keeps public dashboard traffic within free-tier-friendly query volume.",
    },
]

QUALITY_GATES: list[dict[str, str]] = [
    {"gate": "Raw row count reconciliation", "expected_result": "PASS before presentation"},
    {"gate": "Reporting table readiness", "expected_result": "PASS before presentation"},
    {"gate": "Model score contract", "expected_result": "PASS before release"},
    {"gate": "Threshold simulation contract", "expected_result": "PASS before release"},
    {"gate": "English public surface scan", "expected_result": "PASS before deployment"},
]

MODEL_VALIDATION_METRICS: list[dict[str, str]] = [
    {"metric": "Validation design", "value": "Time-based holdout", "interpretation": "Reduces leakage risk from relative transaction time."},
    {"metric": "ROC-AUC", "value": "0.9167", "interpretation": "Strong ranking performance across score thresholds."},
    {"metric": "Average precision", "value": "0.5308", "interpretation": "More informative than accuracy for the 3.5% fraud base rate."},
    {"metric": "Top decile lift", "value": "7.24x", "interpretation": "The highest-score decile contains materially more fraud than the baseline."},
    {"metric": "Feature count", "value": "206", "interpretation": "Model uses engineered transaction, card, identity, amount, and masked feature signals."},
]

ANALYSIS_COVERAGE: list[dict[str, str]] = [
    {"area": "Data reliability", "dashboard_evidence": "Data Trust", "status": "Covered", "primary_output": "Row-count contract, duplicate protection, missingness, readiness gate."},
    {"area": "Executive summary", "dashboard_evidence": "Executive Overview", "status": "Covered", "primary_output": "Portfolio KPIs, exposure lens, management message."},
    {"area": "Segment concentration", "dashboard_evidence": "Executive Overview / Segment Explorer", "status": "Covered", "primary_output": "Product risk, lift, fraud share, Pareto, watchlist."},
    {"area": "Identity coverage", "dashboard_evidence": "Segment Explorer", "status": "Covered", "primary_output": "Identity-present versus identity-missing fraud rates and product coverage."},
    {"area": "Amount analysis", "dashboard_evidence": "Executive Overview / Segment Explorer", "status": "Covered", "primary_output": "Amount bands, amount-at-risk lens, decimal amount pattern."},
    {"area": "Relative time", "dashboard_evidence": "Executive Overview / Segment Explorer", "status": "Covered", "primary_output": "Relative day drift and relative hour monitoring windows."},
    {"area": "Payment and email", "dashboard_evidence": "Segment Explorer", "status": "Covered", "primary_output": "Payment heatmap and purchaser email risk groups."},
    {"area": "Feature engineering", "dashboard_evidence": "Model Operations / Data Trust", "status": "Covered", "primary_output": "Feature importance, feature families, missingness, masked-feature caveats."},
    {"area": "ML performance", "dashboard_evidence": "Model Operations", "status": "Covered", "primary_output": "ROC-AUC, average precision, top-decile lift, threshold confusion matrix."},
    {"area": "Threshold operations", "dashboard_evidence": "Model Operations", "status": "Covered", "primary_output": "Workload, fraud capture, precision, false-positive and false-negative exposure."},
    {"area": "Business impact", "dashboard_evidence": "Model Operations", "status": "Covered", "primary_output": "Review cost, missed exposure, capacity status, policy recommendation."},
    {"area": "Presentation readiness", "dashboard_evidence": "Data Trust", "status": "Covered", "primary_output": "Readiness checks, KPI dictionary, methodology controls."},
]

HYPOTHESIS_REGISTER: list[dict[str, str]] = [
    {
        "hypothesis": "Fraud is low at portfolio level but concentrated in a small number of actionable segments.",
        "evidence": "Segment watchlist, fraud contribution waterfall, Pareto concentration.",
        "decision": "Prioritize segment-based monitoring rather than portfolio-average rules.",
    },
    {
        "hypothesis": "Product, identity, payment, and email fields create fraud separation.",
        "evidence": "Product risk, identity coverage matrix, payment heatmap, email domain risk.",
        "decision": "Use segment lift and fraud share together for rule calibration.",
    },
    {
        "hypothesis": "TransactionDT must be treated as relative time.",
        "evidence": "Daily drift and relative-hour panels use elapsed day/hour language only.",
        "decision": "Do not make calendar-date claims from TransactionDT.",
    },
    {
        "hypothesis": "Identity availability is both a coverage metric and a behavioral risk signal.",
        "evidence": "Identity-present and identity-missing fraud rates are tracked separately.",
        "decision": "Monitor identity coverage as a first-class signal.",
    },
    {
        "hypothesis": "Model score should prioritize review queues, not automate decline decisions.",
        "evidence": "Threshold simulation, confusion matrix, capacity and cost assumptions.",
        "decision": "Use score bands as triage policy inputs.",
    },
]

EXECUTIVE_TAKEAWAYS: list[dict[str, str]] = [
    {
        "takeaway": "Fraud is concentrated, not evenly distributed.",
        "evidence": "Product, identity, amount, payment, and email cuts show materially different lift and fraud-share profiles.",
        "decision": "Manage fraud through segment-specific monitoring instead of a single portfolio-average rule.",
    },
    {
        "takeaway": "Identity availability is an analytical signal.",
        "evidence": "Identity-present transactions carry higher observed fraud intensity, while identity coverage varies sharply by ProductCD.",
        "decision": "Track identity coverage and identity-present risk as separate operating controls.",
    },
    {
        "takeaway": "Model score is a triage layer.",
        "evidence": "Threshold simulation converts score cutoffs into workload, capture, precision, false positives, and missed exposure.",
        "decision": "Use score bands to prioritize analyst queues; do not position the model as an autonomous decline engine.",
    },
]

DATA_DICTIONARY: list[dict[str, str]] = [
    {
        "field": "TransactionID",
        "business_meaning": "Unique transaction key used for reconciliation, joins, and duplicate controls.",
        "interpretation_note": "Must remain unique after transaction and identity joins.",
    },
    {
        "field": "TransactionDT",
        "business_meaning": "Elapsed seconds from an unknown reference point.",
        "interpretation_note": "Use only as relative day/hour. Do not make calendar-date claims.",
    },
    {
        "field": "TransactionAmt",
        "business_meaning": "Transaction amount used for ticket-size bands and amount exposure analysis.",
        "interpretation_note": "Analyze both amount bands and decimal/round amount behavior.",
    },
    {
        "field": "ProductCD",
        "business_meaning": "Masked product/channel category supplied by the dataset owner.",
        "interpretation_note": "Use as a segmentation signal; do not assign unsupported real-world product names.",
    },
    {
        "field": "card1-card6",
        "business_meaning": "Masked card-related attributes.",
        "interpretation_note": "High model importance supports predictive value, not a confirmed business definition.",
    },
    {
        "field": "addr1-addr2",
        "business_meaning": "Masked address-related attributes.",
        "interpretation_note": "Used in synthetic UID and segment diagnostics where available.",
    },
    {
        "field": "P_emaildomain / R_emaildomain",
        "business_meaning": "Purchaser and recipient email domain groups.",
        "interpretation_note": "Grouped into monitoring categories for explainable operations.",
    },
    {
        "field": "C1-C14",
        "business_meaning": "Masked count-style engineered features.",
        "interpretation_note": "Treat as observational signals, not as confirmed customer behavior definitions.",
    },
    {
        "field": "D1-D15",
        "business_meaning": "Masked time-delta style engineered features.",
        "interpretation_note": "Useful for model ranking and drift monitoring, but interpretation remains limited.",
    },
    {
        "field": "M1-M9",
        "business_meaning": "Masked match indicators.",
        "interpretation_note": "Monitor missingness and importance by family rather than over-explaining individual fields.",
    },
    {
        "field": "V1-V339",
        "business_meaning": "Anonymized Vesta-engineered relationship/count/ranking features.",
        "interpretation_note": "Feature selection and missingness handling must be documented because these fields are heavily masked.",
    },
    {
        "field": "risk_band",
        "business_meaning": "Operational band derived from model score quantiles.",
        "interpretation_note": "Used for queue priority, not for automatic decline decisions.",
    },
]

MODEL_REPRODUCIBILITY: list[dict[str, str]] = [
    {
        "artifact": "outputs/tables/validation_predictions.csv",
        "purpose": "Validation labels and predicted probabilities used to recompute ROC-AUC, average precision, threshold metrics, and calibration.",
    },
    {
        "artifact": "outputs/tables/feature_importance.csv",
        "purpose": "LightGBM feature importance export used for feature-family explainability.",
    },
    {
        "artifact": "scripts/generate_model_evidence.py",
        "purpose": "Recomputes model evidence from exported validation artifacts and writes portfolio-ready documentation.",
    },
]

app = FastAPI(
    title="Fraud Analytics Live Dashboard",
    description="Live API over the dbt-built BigQuery reporting layer.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("WEB_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def project_id() -> str:
    value = os.getenv("GCP_PROJECT_ID") or os.getenv("BQ_PROJECT_ID")
    if not value:
        raise RuntimeError("Set GCP_PROJECT_ID or BQ_PROJECT_ID before starting the dashboard API.")
    return value


def project_label() -> str:
    configured = os.getenv("GCP_PROJECT_ID") or os.getenv("BQ_PROJECT_ID")
    if configured:
        return configured
    if data_backend() == "duckdb":
        return "local-duckdb"
    return "unconfigured"


def dataset_id() -> str:
    return os.getenv("BQ_DATASET", DEFAULT_DATASET)


def data_backend() -> str:
    return os.getenv("WEB_DATA_BACKEND", "bigquery").strip().lower()


def duckdb_path() -> str:
    return os.getenv("FRAUD_PROJECT_DUCKDB_PATH", DEFAULT_DUCKDB_PATH)


def bigquery_location() -> str | None:
    return os.getenv("BIGQUERY_LOCATION") or os.getenv("BQ_LOCATION")


def max_bytes_billed() -> int | None:
    raw_value = os.getenv("BIGQUERY_MAX_BYTES_BILLED")
    return int(raw_value) if raw_value else None


def qualified_table(table_name: str) -> str:
    if table_name not in set(BIGQUERY_TABLES.values()):
        raise ValueError(f"Table is not allowlisted: {table_name}")
    return f"`{project_id()}.{dataset_id()}.{table_name}`"


def qualified_duckdb_table(table_name: str) -> str:
    if table_name not in set(BIGQUERY_TABLES.values()):
        raise ValueError(f"Table is not allowlisted: {table_name}")
    return f'"{DUCKDB_SCHEMA}"."{table_name}"'


@lru_cache(maxsize=1)
def bq_client() -> bigquery.Client:
    raw_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    encoded_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON_B64")
    if encoded_credentials:
        raw_credentials = base64.b64decode(encoded_credentials).decode("utf-8")

    if raw_credentials:
        credentials_info = json.loads(raw_credentials)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )
        return bigquery.Client(project=project_id(), location=bigquery_location(), credentials=credentials)

    return bigquery.Client(project=project_id(), location=bigquery_location())


def query_job_config() -> bigquery.QueryJobConfig:
    config = bigquery.QueryJobConfig(use_query_cache=True)
    billed = max_bytes_billed()
    if billed:
        config.maximum_bytes_billed = billed
    return config


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value


def rows_to_dicts(rows: bigquery.table.RowIterator) -> list[dict[str, Any]]:
    return [
        {key: to_jsonable(value) for key, value in dict(row).items()}
        for row in rows
    ]


def run_query(sql: str) -> list[dict[str, Any]]:
    if data_backend() == "duckdb":
        return run_duckdb_query(sql)

    try:
        rows = bq_client().query(sql, job_config=query_job_config()).result()
    except GoogleAPIError as exc:
        raise HTTPException(status_code=502, detail=f"BigQuery query failed: {exc.message}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return rows_to_dicts(rows)


def run_duckdb_query(sql: str) -> list[dict[str, Any]]:
    try:
        import duckdb

        with duckdb.connect(duckdb_path(), read_only=True) as connection:
            result = connection.execute(sql)
            columns = [column[0] for column in result.description]
            return [
                {column: to_jsonable(value) for column, value in zip(columns, row, strict=True)}
                for row in result.fetchall()
            ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DuckDB query failed: {exc}") from exc


def public_family(value: Any) -> str:
    raw = str(value or "").lower()
    if "identity" in raw:
        return "Identity"
    if "amount" in raw or "band" in raw:
        return "Amount band"
    if "payment" in raw:
        return "Payment"
    if "email" in raw:
        return "Email domain"
    if "risk" in raw:
        return "Risk band"
    if "product" in raw or any(ord(char) > 127 for char in raw):
        return "Product"
    return str(value or "Segment")


def public_priority(value: Any) -> str:
    raw = str(value or "").lower()
    if "critical" in raw:
        return "Critical"
    if "high" in raw:
        return "High"
    if "monitor" in raw:
        return "Monitor"
    return "Normal" if raw else "Monitor"


def action_for_priority(family: str, priority: str) -> str:
    if priority == "Critical":
        return f"{family} requires immediate review, rule calibration, and capacity allocation."
    if priority == "High":
        return f"{family} should enter the daily review queue with trend and volume monitoring."
    if priority == "Monitor":
        return f"{family} should be sampled weekly and tracked for drift or volume expansion."
    return f"{family} remains in standard monitoring with no additional friction unless drift increases."


def risk_band_review_priority(risk_band: Any) -> str:
    return {
        "Critical": "Immediate review",
        "High": "Same-day priority",
        "Elevated": "Queue sampling",
        "Low": "Standard monitoring",
    }.get(str(risk_band), "Standard monitoring")


def queue_policy(risk_band: Any) -> str:
    return {
        "Critical": "Real-time manual review queue",
        "High": "Same-day priority review",
        "Elevated": "Sample-based manual control",
        "Low": "Automated monitoring",
    }.get(str(risk_band), "Automated monitoring")


def management_note(risk_band: Any) -> str:
    return {
        "Critical": "Reserve analyst capacity",
        "High": "Reserve analyst capacity",
        "Elevated": "Monitor rule performance weekly",
        "Low": "No additional action required",
    }.get(str(risk_band), "No additional action required")


def public_drift_flag(value: Any) -> str:
    raw = str(value or "").lower()
    if "high" in raw:
        return "High risk drift"
    if "low" in raw:
        return "Low risk drift"
    return "Normal band"


def operating_mode(value: Any) -> str:
    raw = str(value or "").lower()
    if "broad" in raw:
        return "Broad monitoring"
    if "balanced" in raw:
        return "Balanced operations"
    if "focused" in raw or "priority" in raw:
        return "Focused risk queue"
    if "narrow" in raw or "critical" in raw:
        return "Narrow critical queue"
    return str(value or "Balanced operations")


READINESS_COPY: dict[int, tuple[str, str, str]] = {
    1: ("Data reliability", "Raw train transaction row count", "Ready for presentation"),
    2: ("Dashboard contract", "Web dashboard fact row count", "Ready for presentation"),
    3: ("Executive presentation", "Report narrative coverage", "Ready for presentation"),
    4: ("Risk analytics", "Segment watchlist coverage", "Ready for presentation"),
    5: ("Model operations", "Risk band operations strategy", "Ready for presentation"),
    6: ("Model operations", "Threshold simulation", "Ready for presentation"),
}

NARRATIVE_COPY: dict[int, dict[str, str]] = {
    1: {
        "page_name": "Executive Overview",
        "executive_message": "Fraud is rare at portfolio level, but it concentrates in a manageable set of segments.",
        "analytical_focus": "Use total volume, baseline fraud rate, product lift, identity lift, and risk-band lift as the first executive readout.",
        "recommended_action": "Prioritize Product C, identity-present transactions, and high-lift risk bands for operational monitoring.",
    },
    2: {
        "page_name": "Segment Explorer",
        "executive_message": "Product and identity fields create the clearest separation between baseline and elevated risk.",
        "analytical_focus": "Compare product, identity, payment, email, and amount segments by fraud rate, lift, and fraud share.",
        "recommended_action": "Use the segment watchlist as the weekly risk committee monitoring queue.",
    },
    3: {
        "page_name": "Amount and Time Signals",
        "executive_message": "Amount and relative time behavior are nonlinear and should not be reduced to a single static threshold.",
        "analytical_focus": "Read amount bands, daily drift, relative hour, and amount decimal signals together.",
        "recommended_action": "Tune operating thresholds by relative time window and ticket-size behavior.",
    },
    4: {
        "page_name": "Payment and Email Segments",
        "executive_message": "Payment and email dimensions add explainable monitoring cuts for fraud operations.",
        "analytical_focus": "Compare card network, card type, and purchaser email groups by fraud rate and contribution.",
        "recommended_action": "Monitor high-lift payment/email combinations together with product and model risk bands.",
    },
    5: {
        "page_name": "Model Operations",
        "executive_message": "Model scores convert the analysis into review queues, not autonomous decline decisions.",
        "analytical_focus": "Evaluate risk bands, threshold simulation, review workload, fraud capture, precision, and feature importance.",
        "recommended_action": "Use High and Critical queues as the first operating point, then recalibrate by capacity and cost.",
    },
    6: {
        "page_name": "Data Trust",
        "executive_message": "Data quality and lineage are part of the fraud report's control evidence.",
        "analytical_focus": "Show row-count contracts, readiness checks, missingness, and dbt-to-dashboard lineage.",
        "recommended_action": "Keep dbt tests and dashboard readiness checks as release gates before executive review.",
    },
}


def public_sequence_key(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        digits = "".join(char for char in str(value or "") if char.isdigit())
        return int(digits[-3:]) if digits else 0


def normalize_public_row(table_key: str, row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)

    if "segment_family" in normalized:
        normalized["segment_family"] = public_family(normalized.get("segment_family"))
    if "risk_priority" in normalized:
        normalized["risk_priority"] = public_priority(normalized.get("risk_priority"))
    if table_key == "segment_watchlist":
        family = public_family(normalized.get("segment_family"))
        priority = public_priority(normalized.get("risk_priority"))
        normalized["segment_family"] = family
        normalized["risk_priority"] = priority
        normalized["recommended_action"] = action_for_priority(family, priority)

    if table_key in {"review_strategy", "model_risk_bands"}:
        normalized["review_priority"] = risk_band_review_priority(normalized.get("risk_band"))
    if table_key == "review_strategy":
        normalized["queue_policy"] = queue_policy(normalized.get("risk_band"))
        normalized["management_note"] = management_note(normalized.get("risk_band"))

    if table_key == "daily_drift" and "drift_flag" in normalized:
        normalized["drift_flag"] = public_drift_flag(normalized.get("drift_flag"))

    if table_key == "threshold_simulation" and "operating_mode" in normalized:
        normalized["operating_mode"] = operating_mode(normalized.get("operating_mode"))

    if table_key == "report_readiness":
        copy = READINESS_COPY.get(public_sequence_key(normalized.get("check_id")))
        if copy:
            normalized["readiness_area"] = copy[0]
            normalized["check_name"] = copy[1]
            normalized["readiness_result"] = copy[2] if normalized.get("status") == "PASS" else "Action required"

    if table_key == "report_narrative":
        copy = NARRATIVE_COPY.get(public_sequence_key(normalized.get("page_order")))
        if copy:
            normalized.update(copy)

    return normalized


_CACHE: dict[str, Any] = {"expires_at": 0.0, "payload": None}


def build_dashboard_payload() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, table_name in BIGQUERY_TABLES.items():
        table = qualified_duckdb_table(table_name) if data_backend() == "duckdb" else qualified_table(table_name)
        data[key] = [
            normalize_public_row(key, row)
            for row in run_query(TABLE_QUERIES[key].format(table=table))
        ]

    kpis = data["executive_kpis"][0] if data["executive_kpis"] else {}
    readiness = data["report_readiness"]
    data["meta"] = {
        "project_id": project_label(),
        "backend": data_backend(),
        "dataset": dataset_id(),
        "table_count": len(BIGQUERY_TABLES),
        "total_transactions": kpis.get("total_transactions"),
        "fraud_transactions": kpis.get("fraud_transactions"),
        "readiness_passed": sum(1 for row in readiness if row.get("status") == "PASS"),
        "readiness_total": len(readiness),
        "refreshed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    return data


@app.get("/api/metadata")
def metadata() -> dict[str, Any]:
    return {
        "product": "Fraud Risk Intelligence",
        "presentation_layer": "web_dashboard",
        "backend": data_backend(),
        "project_id": project_label(),
        "dataset": dataset_id(),
        "table_count": len(BIGQUERY_TABLES),
        "table_groups": BIGQUERY_TABLES,
        "kpi_definitions": KPI_DEFINITIONS,
        "methodology_notes": METHODOLOGY_NOTES,
        "operating_assumptions": OPERATING_ASSUMPTIONS,
        "model_validation_metrics": MODEL_VALIDATION_METRICS,
        "analysis_coverage": ANALYSIS_COVERAGE,
        "hypothesis_register": HYPOTHESIS_REGISTER,
        "executive_takeaways": EXECUTIVE_TAKEAWAYS,
        "data_dictionary": DATA_DICTIONARY,
        "model_reproducibility": MODEL_REPRODUCIBILITY,
        "data_contract": {
            "source": "IEEE-CIS Fraud Detection",
            "reporting_dataset": dataset_id(),
            "refresh_mode": "dbt-built reporting tables with cached FastAPI delivery",
            "owner": "Fraud Analytics Team",
            "release_rule": "All quality gates must pass before executive presentation.",
            "raw_access_policy": "The public dashboard reads only allowlisted reporting marts.",
        },
        "quality_gates": QUALITY_GATES,
        "refreshed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


@app.get("/api/dashboard")
def dashboard(refresh: bool = Query(default=False)) -> dict[str, Any]:
    now = time.time()
    if not refresh and _CACHE["payload"] is not None and _CACHE["expires_at"] > now:
        return _CACHE["payload"]

    payload = build_dashboard_payload()
    cache_seconds = int(os.getenv("WEB_CACHE_SECONDS", str(DEFAULT_CACHE_SECONDS)))
    _CACHE["payload"] = payload
    _CACHE["expires_at"] = now + cache_seconds
    return payload


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "backend": data_backend(),
        "project_configured": bool(os.getenv("GCP_PROJECT_ID") or os.getenv("BQ_PROJECT_ID") or data_backend() == "duckdb"),
        "dataset": dataset_id(),
        "duckdb_path": duckdb_path() if data_backend() == "duckdb" else None,
        "location": bigquery_location() or "default",
        "cache_seconds": int(os.getenv("WEB_CACHE_SECONDS", str(DEFAULT_CACHE_SECONDS))),
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
