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


NICHE_DIMENSIONS: dict[str, str] = {
    "Product": "product_segment",
    "Amount band": "amount_segment",
    "Payment": "payment_segment",
    "Email domain": "email_segment",
    "Identity": "identity_segment",
    "Risk band": "risk_segment",
}


def niche_select(parent_family: str, child_family: str) -> str:
    parent_col = NICHE_DIMENSIONS[parent_family]
    child_col = NICHE_DIMENSIONS[child_family]
    return (
        "select "
        f"'{parent_family}' as parent_family, "
        f"{parent_col} as parent_segment, "
        f"'{child_family}' as child_family, "
        f"{child_col} as child_segment, "
        "count(*) as transaction_count, "
        "sum(is_fraud) as fraud_count, "
        "case when count(*) = 0 then 0 else sum(is_fraud) * 1.0 / count(*) end as fraud_rate, "
        "avg(transaction_amount) as avg_transaction_amount "
        "from base "
        f"group by {parent_col}, {child_col}"
    )


NICHE_DRILLDOWN_QUERY = (
    "with base as ("
    "select "
    "coalesce(product_cd, 'Unknown') as product_segment, "
    "coalesce(amount_band, 'Unknown') as amount_segment, "
    "concat(coalesce(card_network, 'Unknown'), ' / ', coalesce(card_type, 'Unknown')) as payment_segment, "
    "coalesce(purchaser_email_group, 'Unknown') as email_segment, "
    "case when has_identity = 1 then 'Identity present' else 'Identity missing' end as identity_segment, "
    "coalesce(risk_band, 'Unscored') as risk_segment, "
    "transaction_amount, "
    "is_fraud "
    "from {table}"
    ") "
    + " union all ".join(
        niche_select(parent_family, child_family)
        for parent_family in NICHE_DIMENSIONS
        for child_family in NICHE_DIMENSIONS
        if parent_family != child_family
    )
)


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
    "niche_drilldown": NICHE_DRILLDOWN_QUERY,
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
    "niche_drilldown": "fact_train_transactions",
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
        "purpose": "Keeps public dashboard traffic within cost-controlled query volume.",
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
    {"metric": "Brier score", "value": "0.0654", "interpretation": "Probability calibration error; lower is better and should be tracked before production decisioning."},
    {"metric": "Expected calibration error", "value": "14.87%", "interpretation": "Weighted score-to-observed-rate gap across validation deciles."},
    {"metric": "KS statistic", "value": "67.81%", "interpretation": "Maximum score-distribution separation between fraud and legitimate transactions."},
    {"metric": "Top decile lift", "value": "7.24x", "interpretation": "The highest-score decile contains materially more fraud than the baseline."},
    {"metric": "p95 precision", "value": "40.72%", "interpretation": "Precision for the validation top 5% review queue."},
    {"metric": "p95 recall", "value": "59.18%", "interpretation": "Fraud labels captured by the validation top 5% review queue."},
    {"metric": "Feature count", "value": "206", "interpretation": "Model uses engineered transaction, card, identity, amount, and masked feature signals."},
]

THRESHOLD_DECISION_POLICY: list[dict[str, str]] = [
    {
        "rule": "Primary operating rule",
        "decision": "Start with the smallest review queue that meets the fraud-capture target while staying inside analyst capacity.",
        "evidence": "The dashboard recalculates capture, precision, workload, false-positive cost, and missed exposure from the selected threshold.",
    },
    {
        "rule": "Capacity breach",
        "decision": "If daily reviews exceed available capacity, raise the score threshold or restrict operations to High and Critical segments.",
        "evidence": "The capacity simulator compares selected-threshold daily workload against the analyst capacity input.",
    },
    {
        "rule": "Capture shortfall",
        "decision": "If capture falls below the risk committee target, lower the threshold and offset workload through segment prioritization.",
        "evidence": "The threshold curve exposes the tradeoff between fraud capture, precision, and review volume.",
    },
    {
        "rule": "Model-risk control",
        "decision": "Use scores for triage and prioritization only until probability calibration and decision logs are approved.",
        "evidence": "Brier score and expected calibration error are tracked as governance metrics.",
    },
]

BUSINESS_IMPACT_SCENARIOS: list[dict[str, str]] = [
    {
        "scenario": "Base pilot",
        "assumption": "$4 review cost and $120 missed-fraud loss.",
        "management_use": "Default dashboard scenario for weekly risk committee discussion.",
    },
    {
        "scenario": "High review cost",
        "assumption": "Review cost doubles while fraud loss remains constant.",
        "management_use": "Tests whether the selected queue still makes sense when operations are constrained.",
    },
    {
        "scenario": "High fraud loss",
        "assumption": "Missed-fraud loss doubles while review cost remains constant.",
        "management_use": "Tests whether the bank should lower threshold and accept more manual review.",
    },
    {
        "scenario": "Stress case",
        "assumption": "Review cost and missed-fraud loss both double.",
        "management_use": "Documents the decision boundary before production pilot approval.",
    },
]

MODEL_GOVERNANCE_CONTROLS: list[dict[str, str]] = [
    {
        "control": "Purpose limitation",
        "owner": "Fraud strategy",
        "evidence": "The model is positioned as queue prioritization, not autonomous decline.",
    },
    {
        "control": "Threshold approval",
        "owner": "Risk committee",
        "evidence": "Threshold must be selected with capacity, precision, capture, and loss assumptions visible.",
    },
    {
        "control": "Calibration review",
        "owner": "Model risk",
        "evidence": "Brier score, calibration gaps, and expected calibration error are tracked before production decisioning.",
    },
    {
        "control": "Masked-feature interpretation",
        "owner": "Analytics lead",
        "evidence": "Vesta-engineered fields are described as observational signals, not confirmed business definitions.",
    },
    {
        "control": "Auditability",
        "owner": "Data platform",
        "evidence": "dbt tests, reporting readiness checks, and validation artifacts provide a release trail.",
    },
]

MONITORING_PLAYBOOK: list[dict[str, str]] = [
    {
        "trigger": "Fraud drift",
        "condition": "Relative-day fraud rate moves outside the expected monitoring band.",
        "action": "Review recent product, amount, payment, and email segment shifts before changing customer friction.",
    },
    {
        "trigger": "Queue pressure",
        "condition": "Selected-threshold daily workload exceeds analyst capacity.",
        "action": "Raise threshold, split queues by segment priority, or add temporary review coverage.",
    },
    {
        "trigger": "Missingness spike",
        "condition": "A feature family shows materially higher missingness than the baseline scorecard.",
        "action": "Freeze rule expansion until ingestion and feature-engineering checks pass.",
    },
    {
        "trigger": "Calibration degradation",
        "condition": "Brier score or expected calibration error worsens after retraining or schema change.",
        "action": "Keep the model in monitoring mode and recalibrate probabilities before decision use.",
    },
    {
        "trigger": "Readiness failure",
        "condition": "Any reporting release gate fails before an executive review.",
        "action": "Block deployment, rerun dbt build, and reconcile row counts before presentation.",
    },
]

PRODUCTION_VALIDATION: list[dict[str, str]] = [
    {
        "gate": "Live API contract",
        "status": "PASS",
        "evidence": "Production API returns allowlisted reporting groups and the niche drilldown group from fraud_project_reporting.",
    },
    {
        "gate": "Population reconciliation",
        "status": "PASS",
        "evidence": "Reporting fact population equals 590,540 transactions and 20,663 fraud labels.",
    },
    {
        "gate": "Readiness score",
        "status": "PASS",
        "evidence": "Dashboard readiness returns 6/6 release checks.",
    },
    {
        "gate": "Local dbt build",
        "status": "PASS",
        "evidence": "DuckDB development build completed with 132 pass, 0 warn, 0 error, 1 no-op, 133 total.",
    },
    {
        "gate": "Production dbt build",
        "status": "Operator controlled",
        "evidence": "Run with an operator-supplied service account via GOOGLE_APPLICATION_CREDENTIALS; credentials are never committed.",
    },
]

PAGE_ACTION_MESSAGES: list[dict[str, str]] = [
    {
        "page": "Executive Overview",
        "action": "Lead with concentration, not volume.",
        "message": "Use Product, amount, identity, and risk-band concentration to decide where management attention should move first.",
    },
    {
        "page": "Segment Explorer",
        "action": "Calibrate segment rules before adding friction.",
        "message": "Compare lift and fraud share together; high rate alone is not enough if the segment is too small.",
    },
    {
        "page": "Model Operations",
        "action": "Select thresholds as operating policies.",
        "message": "Treat threshold movement as a tradeoff between fraud capture, analyst workload, precision, and missed exposure.",
    },
    {
        "page": "Data Trust",
        "action": "Keep release gates visible.",
        "message": "Readiness, row-count reconciliation, missingness, and calibration controls are part of the fraud product, not background checks.",
    },
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


def cached_dashboard_payload(refresh: bool = False) -> dict[str, Any]:
    now = time.time()
    if not refresh and _CACHE["payload"] is not None and _CACHE["expires_at"] > now:
        return _CACHE["payload"]

    payload = build_dashboard_payload()
    cache_seconds = int(os.getenv("WEB_CACHE_SECONDS", str(DEFAULT_CACHE_SECONDS)))
    _CACHE["payload"] = payload
    _CACHE["expires_at"] = now + cache_seconds
    return payload


def enterprise_table(table_name: str) -> str:
    return qualified_duckdb_table(table_name) if data_backend() == "duckdb" else qualified_table(table_name)


def risk_category_from_band(value: Any) -> str:
    return {
        "Critical": "Critical",
        "High": "High Risk",
        "Elevated": "Medium Risk",
        "Low": "Low Risk",
    }.get(str(value or ""), "Safe")


def recommended_action_from_band(value: Any) -> str:
    return {
        "Critical": "Immediate manual review",
        "High": "Same-day analyst review",
        "Elevated": "Sample and monitor",
        "Low": "Standard monitoring",
    }.get(str(value or ""), "Standard monitoring")


def risk_score_sql() -> str:
    return (
        "case "
        "when risk_band = 'Critical' then least(100, 90 + coalesce(predicted_fraud_probability, 0) * 10) "
        "when risk_band = 'High' then least(89, 72 + coalesce(predicted_fraud_probability, 0) * 18) "
        "when risk_band = 'Elevated' then least(69, 45 + coalesce(predicted_fraud_probability, 0) * 25) "
        "when risk_band = 'Low' then least(44, 15 + coalesce(predicted_fraud_probability, 0) * 25) "
        "else least(19, coalesce(predicted_fraud_probability, 0) * 100) "
        "end"
    )


def case_queue_sql(limit: int = 150) -> str:
    table = enterprise_table("fact_train_transactions")
    safe_limit = max(10, min(int(limit), 500))
    score = risk_score_sql()
    return f"""
with base as (
    select
        transaction_id,
        transaction_day,
        transaction_hour,
        transaction_amount,
        amount_band,
        product_cd,
        card_network,
        card_type,
        device_type,
        purchaser_email_group,
        has_identity,
        synthetic_uid_card_addr,
        is_fraud,
        predicted_fraud_probability,
        coalesce(risk_band, 'Unscored') as risk_band
    from {table}
    where predicted_fraud_probability is not null
),
entity_stats as (
    select
        synthetic_uid_card_addr,
        count(*) as entity_transaction_count,
        sum(coalesce(is_fraud, 0)) as entity_prior_fraud_proxy
    from base
    where synthetic_uid_card_addr is not null
    group by 1
)
select
    b.transaction_id,
    b.transaction_day,
    b.transaction_hour,
    b.transaction_amount,
    b.amount_band,
    b.product_cd,
    b.card_network,
    b.card_type,
    b.device_type,
    b.purchaser_email_group,
    case when b.has_identity = 1 then 'Identity present' else 'Identity missing' end as identity_status,
    b.is_fraud,
    b.predicted_fraud_probability as model_probability,
    b.risk_band,
    {score} as risk_score,
    case
        when b.risk_band = 'Critical' then 'Critical'
        when b.risk_band = 'High' then 'High Risk'
        when b.risk_band = 'Elevated' then 'Medium Risk'
        when b.risk_band = 'Low' then 'Low Risk'
        else 'Safe'
    end as risk_category,
    abs(coalesce(b.predicted_fraud_probability, 0) - 0.5) * 2 as model_confidence,
    coalesce(e.entity_prior_fraud_proxy, 0) as entity_prior_fraud_proxy,
    coalesce(e.entity_transaction_count, 1) as entity_transaction_count,
    case
        when b.risk_band = 'Critical' then 'Immediate manual review'
        when b.risk_band = 'High' then 'Same-day analyst review'
        when b.risk_band = 'Elevated' then 'Sample and monitor'
        else 'Standard monitoring'
    end as recommended_action,
    case
        when b.risk_band = 'Critical' then 'P0'
        when b.risk_band = 'High' then 'P1'
        when b.risk_band = 'Elevated' then 'P2'
        else 'P3'
    end as sla_priority
from base as b
left join entity_stats as e
    on b.synthetic_uid_card_addr = e.synthetic_uid_card_addr
order by
    case b.risk_band
        when 'Critical' then 1
        when 'High' then 2
        when 'Elevated' then 3
        when 'Low' then 4
        else 5
    end,
    b.predicted_fraud_probability desc,
    b.transaction_amount desc
limit {safe_limit}
"""


def transaction_detail_sql(transaction_id: int) -> str:
    table = enterprise_table("fact_train_transactions")
    score = risk_score_sql()
    return f"""
select
    transaction_id,
    transaction_day,
    transaction_week,
    transaction_hour,
    relative_day_of_week,
    time_window,
    transaction_amount,
    transaction_amount_cents,
    is_round_amount,
    amount_band,
    product_cd,
    card_network,
    card_type,
    device_type,
    purchaser_email_group,
    purchaser_email_risk_group,
    case when has_identity = 1 then 'Identity present' else 'Identity missing' end as identity_status,
    synthetic_uid_card_addr,
    is_fraud,
    predicted_fraud_probability as model_probability,
    coalesce(risk_band, 'Unscored') as risk_band,
    {score} as risk_score,
    case
        when risk_band = 'Critical' then 'Critical'
        when risk_band = 'High' then 'High Risk'
        when risk_band = 'Elevated' then 'Medium Risk'
        when risk_band = 'Low' then 'Low Risk'
        else 'Safe'
    end as risk_category
from {table}
where transaction_id = {int(transaction_id)}
limit 1
"""


def direct_aggregate(sql: str) -> list[dict[str, Any]]:
    return run_query(sql)


def build_transaction_explanation(row: dict[str, Any]) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    probability = float(row.get("model_probability") or 0)
    amount = float(row.get("transaction_amount") or 0)
    if row.get("risk_band") in {"Critical", "High"}:
        factors.append({"factor": "Model risk band", "direction": "Raises risk", "impact": "High", "detail": f"{row.get('risk_band')} queue priority"})
    if amount >= 250:
        factors.append({"factor": "High ticket size", "direction": "Raises risk", "impact": "Medium", "detail": f"Amount {amount:,.0f}"})
    if row.get("identity_status") == "Identity present":
        factors.append({"factor": "Identity signal present", "direction": "Requires review", "impact": "Medium", "detail": "Identity availability is monitored as a risk signal"})
    if str(row.get("purchaser_email_group") or "").lower() in {"anonymous.com", "unknown", "other"}:
        factors.append({"factor": "Email domain group", "direction": "Raises uncertainty", "impact": "Medium", "detail": str(row.get("purchaser_email_group") or "Unknown")})
    if probability >= 0.2:
        factors.append({"factor": "Model probability", "direction": "Raises risk", "impact": "High", "detail": f"{probability:.2%} fraud probability"})
    if not factors:
        factors.append({"factor": "Low operational score", "direction": "Standard monitoring", "impact": "Low", "detail": "No critical driver exceeded the review threshold"})
    return factors[:5]


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
        "threshold_decision_policy": THRESHOLD_DECISION_POLICY,
        "business_impact_scenarios": BUSINESS_IMPACT_SCENARIOS,
        "model_governance_controls": MODEL_GOVERNANCE_CONTROLS,
        "monitoring_playbook": MONITORING_PLAYBOOK,
        "production_validation": PRODUCTION_VALIDATION,
        "page_action_messages": PAGE_ACTION_MESSAGES,
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


@app.get("/api/enterprise/summary")
def enterprise_summary(refresh: bool = Query(default=False)) -> dict[str, Any]:
    payload = cached_dashboard_payload(refresh=refresh)
    kpis = (payload.get("executive_kpis") or [{}])[0]
    threshold_rows = payload.get("threshold_simulation") or []
    risk_rows = payload.get("model_risk_bands") or []
    watchlist = payload.get("segment_watchlist") or []
    recommended_threshold = next(
        (row for row in threshold_rows if 0.04 <= float(row.get("score_threshold") or 0) <= 0.10),
        threshold_rows[min(len(threshold_rows) - 1, 5)] if threshold_rows else {},
    )
    return {
        "meta": payload.get("meta", {}),
        "kpis": kpis,
        "recommended_threshold": recommended_threshold,
        "top_segments": watchlist[:8],
        "risk_distribution": risk_rows,
        "model_metrics": MODEL_VALIDATION_METRICS,
        "trust_signals": {
            "model_version": "lightgbm-v1",
            "validation_design": "time-based holdout",
            "data_source": "IEEE-CIS masked e-commerce transaction data",
            "model_use": "review prioritization only",
        },
    }


@app.get("/api/enterprise/cases")
def enterprise_cases(limit: int = Query(default=150, ge=10, le=500)) -> dict[str, Any]:
    rows = direct_aggregate(case_queue_sql(limit=limit))
    return {
        "cases": rows,
        "count": len(rows),
        "risk_categories": ["Critical", "High Risk", "Medium Risk", "Low Risk", "Safe"],
        "unsupported_fields": ["country", "user_age"],
        "note": "Country and user age are not native IEEE-CIS fields and are intentionally omitted.",
    }


@app.get("/api/enterprise/cases/{transaction_id}")
def enterprise_case_detail(transaction_id: int) -> dict[str, Any]:
    rows = direct_aggregate(transaction_detail_sql(transaction_id))
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction not found in reporting fact table.")
    row = rows[0]
    return {
        "transaction": row,
        "explanation": build_transaction_explanation(row),
        "recommended_action": recommended_action_from_band(row.get("risk_band")),
        "audit_trail": [
            {"step": "Scored", "status": "Complete", "owner": "Model pipeline"},
            {"step": "Queued", "status": risk_category_from_band(row.get("risk_band")), "owner": "Fraud operations"},
            {"step": "Analyst decision", "status": "Pending", "owner": "Manual review"},
        ],
    }


@app.get("/api/enterprise/segments")
def enterprise_segments(refresh: bool = Query(default=False)) -> dict[str, Any]:
    payload = cached_dashboard_payload(refresh=refresh)
    fact_table = enterprise_table("fact_train_transactions")
    device_identity_sql = f"""
select
    coalesce(device_type, 'Unknown') as device_type,
    case when has_identity = 1 then 'Identity present' else 'Identity missing' end as identity_status,
    count(*) as transaction_count,
    sum(is_fraud) as fraud_count,
    sum(is_fraud) * 1.0 / nullif(count(*), 0) as fraud_rate
from {fact_table}
group by 1, 2
order by fraud_rate desc
"""
    entity_network_sql = f"""
select
    concat('Product: ', coalesce(product_cd, 'Unknown')) as source,
    concat('Email: ', coalesce(purchaser_email_group, 'Unknown')) as target,
    count(*) as edge_weight,
    sum(is_fraud) as fraud_count,
    sum(is_fraud) * 1.0 / nullif(count(*), 0) as fraud_rate,
    'masked_product_email' as edge_type
from {fact_table}
group by 1, 2
having count(*) >= 1000
order by fraud_count desc, fraud_rate desc
limit 20
"""
    return {
        "segment_watchlist": payload.get("segment_watchlist", []),
        "niche_drilldown": payload.get("niche_drilldown", []),
        "payment_heatmap": payload.get("payment_heatmap", []),
        "time_amount_signals": payload.get("time_amount_signals", []),
        "daily_drift": payload.get("daily_drift", []),
        "device_identity_heatmap": direct_aggregate(device_identity_sql),
        "masked_entity_edges": direct_aggregate(entity_network_sql),
        "note": "Entity graph is built from masked product, email, device, and identity proxies; it is not a real customer network.",
    }


@app.get("/api/enterprise/alerts")
def enterprise_alerts(refresh: bool = Query(default=False)) -> dict[str, Any]:
    payload = cached_dashboard_payload(refresh=refresh)
    alerts: list[dict[str, Any]] = []
    drift_rows = payload.get("daily_drift", [])
    drift = next((row for row in reversed(drift_rows) if row.get("drift_flag") != "Normal band"), None)
    if drift:
        alerts.append({
            "alert_id": "FD-DRIFT-001",
            "severity": "High",
            "segment": f"Relative day {drift.get('transaction_day')}",
            "trigger": "Fraud drift",
            "current_value": drift.get("fraud_rate_ma7") or drift.get("fraud_rate"),
            "threshold": drift.get("baseline_fraud_rate"),
            "recommended_action": "Review segment mix before changing customer friction.",
            "status": "Open",
        })
    queue = next((row for row in payload.get("review_strategy", []) if row.get("risk_band") == "Critical"), None)
    if queue:
        alerts.append({
            "alert_id": "FD-QUEUE-002",
            "severity": "Critical",
            "segment": "Critical risk queue",
            "trigger": "Queue pressure",
            "current_value": queue.get("estimated_daily_review_volume"),
            "threshold": "Analyst capacity input",
            "recommended_action": "Reserve same-day analyst capacity for critical queue.",
            "status": "Open",
        })
    missing = next(iter(payload.get("data_quality", [])), None)
    if missing:
        alerts.append({
            "alert_id": "FD-DQ-003",
            "severity": "Medium",
            "segment": missing.get("column_family"),
            "trigger": "Feature missingness",
            "current_value": missing.get("avg_missing_rate"),
            "threshold": "Feature family baseline",
            "recommended_action": "Validate ingestion and imputation policy before expanding rules.",
            "status": "Monitoring",
        })
    top_segment = next(iter(payload.get("segment_watchlist", [])), None)
    if top_segment:
        alerts.append({
            "alert_id": "FD-SEG-004",
            "severity": top_segment.get("risk_priority", "High"),
            "segment": top_segment.get("segment_name"),
            "trigger": "Segment concentration",
            "current_value": top_segment.get("fraud_share"),
            "threshold": "Top watchlist rank",
            "recommended_action": top_segment.get("recommended_action"),
            "status": "Open",
        })
    return {
        "mode": "historical_replay",
        "note": "IEEE-CIS is a static dataset; alert stream is a historical replay simulation from reporting tables.",
        "alerts": alerts,
    }


@app.get("/api/enterprise/model-monitoring")
def enterprise_model_monitoring(refresh: bool = Query(default=False)) -> dict[str, Any]:
    payload = cached_dashboard_payload(refresh=refresh)
    return {
        "model_version": "lightgbm-v1",
        "last_training_date": "portfolio training artifact",
        "validation_window": "time-based holdout",
        "metrics": MODEL_VALIDATION_METRICS,
        "thresholds": payload.get("threshold_simulation", []),
        "risk_bands": payload.get("model_risk_bands", []),
        "feature_importance": payload.get("feature_importance", []),
        "data_quality": payload.get("data_quality", []),
        "controls": MODEL_GOVERNANCE_CONTROLS,
    }


@app.get("/api/enterprise/metadata")
def enterprise_metadata() -> dict[str, Any]:
    base = metadata()
    base["enterprise_pages"] = [
        "Executive Command Center",
        "Analyst Investigation Queue",
        "Transaction Detail",
        "Fraud Intelligence Center",
        "Model Monitoring",
        "Alert Management",
    ]
    base["unsupported_fields"] = {
        "country": "Not available in IEEE-CIS without external IP or geo enrichment.",
        "user_age": "Not available in IEEE-CIS without customer profile enrichment.",
    }
    return base


@app.get("/api/dashboard")
def dashboard(refresh: bool = Query(default=False)) -> dict[str, Any]:
    return cached_dashboard_payload(refresh=refresh)


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
