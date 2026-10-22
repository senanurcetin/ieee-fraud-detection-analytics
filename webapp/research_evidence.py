"""Read-only publication of versioned aggregate calibration research."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

APP_DIR = Path(__file__).resolve().parent
CALIBRATION_PATH = APP_DIR / "research" / "published-model-calibration.json"
SOURCE_PARITY_PATH = APP_DIR / "research" / "source-parity.json"
router = APIRouter()
METHODS = ("raw", "platt", "isotonic", "constant")


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Invalid research object")
    return value


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_calibration_report(report: Any) -> dict[str, Any]:
    """Reject incomplete runs and nonfinite metrics before public publication."""
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("Unsupported research schema")
    if not isinstance(report.get("model_version"), str) or not report["model_version"]:
        raise ValueError("Missing model version")
    source = _object(report.get("source"))
    if source.get("rows") != 590_540 or source.get("subset_mode") is not False:
        raise ValueError("Research must use the full training population")
    for key in ("transaction_sha256", "identity_sha256", "ordered_rows_sha256"):
        if not re.fullmatch(r"[a-f0-9]{64}", source.get(key, "")):
            raise ValueError("Missing source fingerprint")
    development, final = _object(report.get("development")), _object(report.get("final"))
    folds = development.get("folds")
    if not isinstance(folds, list) or len(folds) < 3:
        raise ValueError("At least three development windows are required")
    selected = development.get("selected_method")
    if selected not in ("platt", "isotonic") or final.get("selected_method") != selected:
        raise ValueError("Final method must be selected in development")
    for evaluation in [*folds, final]:
        evaluation = _object(evaluation)
        windows = _object(evaluation.get("windows"))
        core, calibration, validation = (_object(windows.get(key)) for key in ("core", "calibration", "validation"))
        for window in (core, calibration, validation):
            if not _integer(window.get("rows")) or window["rows"] < 1:
                raise ValueError("Invalid chronological window support")
            low, high = window.get("min_transaction_dt"), window.get("max_transaction_dt")
            if (type(low) not in (int, float) or type(high) not in (int, float)
                    or not math.isfinite(low) or not math.isfinite(high) or low > high):
                raise ValueError("Invalid chronological window")
        if not (core["max_transaction_dt"] < calibration["min_transaction_dt"]
                and calibration["max_transaction_dt"] < validation["min_transaction_dt"]):
            raise ValueError("Research windows overlap")
        metrics = _object(evaluation.get("metrics"))
        for method in METHODS:
            item = _object(metrics.get(method))
            rows, fraud = item.get("rows"), item.get("fraud_count")
            if not _integer(rows) or not _integer(fraud) or not 0 < fraud < rows:
                raise ValueError("Missing two-class evaluation support")
            if rows != validation["rows"] or fraud != validation.get("fraud_count"):
                raise ValueError("Metrics do not describe their chronological window")
            for key in ("roc_auc", "average_precision", "brier_score", "expected_calibration_error"):
                value = item.get(key)
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError("Invalid research metric")
            loss = item.get("log_loss")
            if type(loss) not in (int, float) or not math.isfinite(loss) or loss < 0:
                raise ValueError("Invalid log loss")
            if not isinstance(item.get("reliability_bins"), list) or not item["reliability_bins"]:
                raise ValueError("Missing calibration reliability evidence")
            support = 0
            for bucket in item["reliability_bins"]:
                bucket = _object(bucket)
                if not _integer(bucket.get("count")) or bucket["count"] < 1:
                    raise ValueError("Invalid reliability support")
                support += bucket["count"]
                for key in ("mean_score", "observed_rate"):
                    value = bucket.get(key)
                    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError("Invalid reliability probability")
            if support != rows:
                raise ValueError("Reliability bins omit evaluation records")
    final_start = final["windows"]["validation"]["min_transaction_dt"]
    if any(fold["windows"]["validation"]["max_transaction_dt"] >= final_start for fold in folds):
        raise ValueError("Development selection overlaps final evaluation")
    if sum(window["rows"] for window in final["windows"].values()) != source["rows"]:
        raise ValueError("Final split does not cover the full source")
    acceptance = _object(final.get("acceptance"))
    if not isinstance(acceptance.get("accepted_for_retrospective_probability"), bool):
        raise ValueError("Missing explicit retrospective acceptance decision")
    if _object(report.get("score_contract")).get("not_for_live_decisions") is not True:
        raise ValueError("Research operational boundary is missing")
    if not isinstance(report.get("limitations"), list) or not report["limitations"]:
        raise ValueError("Research limitations are missing")
    # Publication is aggregate-only, including when a future generator changes.
    forbidden = {"predictions", "transactions", "raw_rows", "private_key", "api_token", "records"}

    def inspect(value: Any) -> None:
        if isinstance(value, dict):
            if forbidden.intersection(value):
                raise ValueError("Nonaggregate research payload")
            for item in value.values():
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Nonfinite research payload")

    inspect(report)
    return report


def load_calibration_report(path: Path | None = None) -> dict[str, Any]:
    target = path if path is not None else CALIBRATION_PATH
    # No cache: deletion/replacement cannot leave stale accepted evidence served.
    with target.open("rb") as stream:
        raw = stream.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Research publication exceeds its aggregate size bound")
    evidence = validate_calibration_report(json.loads(raw))
    return {"artifact_sha256": hashlib.sha256(raw).hexdigest(), "evidence": evidence}


def load_source_parity_report(snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind dated source verification to the actual snapshot and query contract."""
    from webapp.main import TABLE_QUERIES

    with SOURCE_PARITY_PATH.open("rb") as stream:
        raw = stream.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Source reconciliation exceeds its publication bound")
    report = _object(json.loads(raw))
    if snapshot is None:
        snapshot = json.loads((APP_DIR / "snapshots" / "dashboard.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if report.get("snapshot_canonical_sha256") != digest:
        raise ValueError("Source reconciliation describes a different snapshot")
    if (report.get("verified_full_27_group_parity") is not True or report.get("report_groups") != 27
            or report.get("sql_query_jobs_submitted") != 0 or report.get("cloud_writes") != 0
            or report.get("snapshot_rewritten") is not False):
        raise ValueError("Source reconciliation is not a complete read-only audit")
    groups = _object(report.get("groups"))
    if groups.keys() != TABLE_QUERIES.keys():
        raise ValueError("Reconciliation omits reporting groups")
    for name, query in TABLE_QUERIES.items():
        group = _object(groups[name])
        if group.get("query_sha256") != hashlib.sha256(query.encode()).hexdigest():
            raise ValueError("Public reporting query changed after reconciliation")
        if group.get("status") not in {"MATCH", "MATCH_WITH_FLOAT_AGGREGATION_TOLERANCE"}:
            raise ValueError("Unresolved source group")
        if group["status"] != "MATCH":
            diagnostic = _object(group.get("floating_aggregation_diagnostic"))
            if diagnostic.get("absolute_tolerance") != 1e-9 or diagnostic.get("relative_tolerance") != 1e-12:
                raise ValueError("Unexpected numeric equivalence policy")
    return {"artifact_sha256": hashlib.sha256(raw).hexdigest(), "evidence": report}


def source_reconciliation_summary(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    try:
        report = load_source_parity_report(snapshot)["evidence"]
        return {key: report[key] for key in (
            "observed_at_utc", "verified_full_27_group_parity", "status_counts", "report_groups",
        )}
    except (OSError, ValueError, TypeError, KeyError):
        return None


@router.get("/api/research/source-parity")
def source_parity_research() -> dict[str, Any]:
    try:
        return load_source_parity_report()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Verified source reconciliation is unavailable") from exc


@router.get("/api/research/calibration")
def calibration_research() -> dict[str, Any]:
    try:
        return load_calibration_report()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Verified calibration research is unavailable") from exc


@router.get("/research", include_in_schema=False)
def research_page() -> FileResponse:
    return FileResponse(APP_DIR / "static" / "research.html")
