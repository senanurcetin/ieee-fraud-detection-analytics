"""FastAPI application for the live fraud analytics web dashboard."""

from __future__ import annotations

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

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

DEFAULT_DATASET = "fraud_project_powerbi"
DEFAULT_CACHE_SECONDS = 600

TABLE_QUERIES: dict[str, str] = {
    "executive_kpis": "select * from {table} limit 1",
    "product_risk": "select * from {table} order by fraud_rate desc",
    "amount_bands": "select * from {table} order by amount_band",
    "daily_drift": "select * from {table} order by transaction_day",
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
    "report_readiness": "select * from {table} order by check_id",
}

BIGQUERY_TABLES: dict[str, str] = {
    "executive_kpis": "pbi_executive_kpis",
    "product_risk": "pbi_product_risk",
    "amount_bands": "pbi_amount_bands",
    "daily_drift": "pbi_daily_drift",
    "payment_heatmap": "pbi_payment_heatmap",
    "email_domain_risk": "pbi_email_domain_risk",
    "model_risk_bands": "pbi_model_risk_bands",
    "feature_importance": "pbi_feature_importance",
    "data_quality": "pbi_data_quality_scorecard",
    "segment_watchlist": "pbi_segment_watchlist",
    "review_strategy": "pbi_review_strategy",
    "threshold_simulation": "pbi_threshold_simulation",
    "report_readiness": "pbi_report_readiness",
}

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


def dataset_id() -> str:
    return os.getenv("BQ_DATASET", DEFAULT_DATASET)


def bigquery_location() -> str | None:
    return os.getenv("BIGQUERY_LOCATION") or os.getenv("BQ_LOCATION")


def max_bytes_billed() -> int | None:
    raw_value = os.getenv("BIGQUERY_MAX_BYTES_BILLED")
    return int(raw_value) if raw_value else None


def qualified_table(table_name: str) -> str:
    if table_name not in set(BIGQUERY_TABLES.values()):
        raise ValueError(f"Table is not allowlisted: {table_name}")
    return f"`{project_id()}.{dataset_id()}.{table_name}`"


@lru_cache(maxsize=1)
def bq_client() -> bigquery.Client:
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
    try:
        rows = bq_client().query(sql, job_config=query_job_config()).result()
    except GoogleAPIError as exc:
        raise HTTPException(status_code=502, detail=f"BigQuery query failed: {exc.message}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return rows_to_dicts(rows)


_CACHE: dict[str, Any] = {"expires_at": 0.0, "payload": None}


def build_dashboard_payload() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, table_name in BIGQUERY_TABLES.items():
        data[key] = run_query(TABLE_QUERIES[key].format(table=qualified_table(table_name)))

    kpis = data["executive_kpis"][0] if data["executive_kpis"] else {}
    readiness = data["report_readiness"]
    data["meta"] = {
        "project_id": project_id(),
        "dataset": dataset_id(),
        "table_count": len(BIGQUERY_TABLES),
        "total_transactions": kpis.get("total_transactions"),
        "fraud_transactions": kpis.get("fraud_transactions"),
        "readiness_passed": sum(1 for row in readiness if row.get("status") == "PASS"),
        "readiness_total": len(readiness),
        "refreshed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    return data


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
        "project_configured": bool(os.getenv("GCP_PROJECT_ID") or os.getenv("BQ_PROJECT_ID")),
        "dataset": dataset_id(),
        "location": bigquery_location() or "default",
        "cache_seconds": int(os.getenv("WEB_CACHE_SECONDS", str(DEFAULT_CACHE_SECONDS))),
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
