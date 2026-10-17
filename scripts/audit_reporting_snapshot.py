"""Deterministic, offline parity audit for published and independently exported reporting payloads.

NO BigQuery SQL, OAuth calls, dbt execution, data refresh, writes to source files,
or cloud billing. A current source JSON must be obtained separately by an
authorized operator; a snapshot compared to itself does not prove freshness.

Usage:
  python scripts/audit_reporting_snapshot.py --output outputs/fraud_parity.json
  python scripts/audit_reporting_snapshot.py --current-json /safe/current_dashboard.json \
      --output outputs/fraud_parity.json

The output deliberately hashes row identifiers and changed values rather than
including raw transaction or segment contents.
"""
from __future__ import annotations

import argparse
import decimal
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "webapp" / "snapshots" / "dashboard.json"
PRECISION = decimal.Decimal("0.000001")
MAX_EXAMPLES = 5

# Mirrors BIGQUERY_TABLES in webapp/main.py; guarded by an offline contract test.
SOURCES: dict[str, str] = {
    "executive_kpis": "rpt_executive_kpis",
    "product_risk": "rpt_product_risk",
    "identity_risk": "rpt_identity_risk",
    "identity_product_coverage": "rpt_identity_product_coverage",
    "amount_bands": "rpt_amount_bands",
    "daily_drift": "rpt_daily_drift",
    "time_amount_signals": "rpt_time_amount_signals",
    "payment_heatmap": "rpt_payment_heatmap",
    "payment_email_matrix": "fact_train_transactions",
    "email_domain_risk": "rpt_email_domain_risk",
    "model_risk_bands": "rpt_model_risk_bands",
    "validation_risk_bands": "rpt_validation_risk_bands",
    "model_calibration": "rpt_model_calibration",
    "feature_importance": "rpt_feature_importance",
    "data_quality": "rpt_data_quality_scorecard",
    "proxy_signal_risk": "rpt_proxy_signal_risk",
    "proxy_product_matrix": "fact_train_transactions",
    "proxy_cross_matrix": "fact_train_transactions",
    "segment_watchlist": "rpt_segment_watchlist",
    "niche_drilldown": "fact_train_transactions",
    "review_strategy": "rpt_review_strategy",
    "threshold_simulation": "rpt_threshold_simulation",
    "validation_threshold_simulation": "rpt_validation_threshold_simulation",
    "segment_model_performance": "rpt_segment_model_performance",
    "report_narrative": "rpt_report_narrative",
    "quality_contract": "rpt_quality_contract",
    "report_readiness": "rpt_report_readiness",
}

# A source-table row is not necessarily equivalent to its presentation group:
# API SQL filters, projections and materialized fact aggregations matter.
SOURCE_SHAPE = {
    "payment_email_matrix": "derived_aggregate",
    "proxy_product_matrix": "derived_aggregate",
    "proxy_cross_matrix": "derived_aggregate",
    "niche_drilldown": "derived_aggregate",
    "data_quality": "derived_aggregate",
    "model_risk_bands": "filtered",
    "feature_importance": "filtered",
}
KEYS: dict[str, tuple[str, ...]] = {
    "executive_kpis": ("total_transactions",),
    "product_risk": ("product_cd",),
    "identity_risk": ("has_identity",),
    "identity_product_coverage": ("product_cd",),
    "amount_bands": ("amount_band",),
    "daily_drift": ("transaction_day",),
    "time_amount_signals": ("transaction_hour", "amount_decimal_group"),
    "payment_heatmap": ("card_network", "card_type"),
    "payment_email_matrix": ("payment_segment", "email_segment"),
    "email_domain_risk": ("purchaser_email_group",),
    "model_risk_bands": ("split", "risk_band"),
    "validation_risk_bands": ("split", "risk_band"),
    "model_calibration": ("score_decile",),
    "feature_importance": ("feature",),
    "data_quality": ("column_family",),
    "proxy_signal_risk": ("proxy_family", "proxy_segment"),
    "proxy_product_matrix": ("proxy_family", "product_cd", "proxy_segment"),
    "proxy_cross_matrix": ("address_proxy_status", "distance_proxy_band"),
    "segment_watchlist": ("watchlist_rank",),
    "niche_drilldown": ("parent_family", "parent_segment", "child_family", "child_segment"),
    "review_strategy": ("risk_band",),
    "threshold_simulation": ("score_threshold",),
    "validation_threshold_simulation": ("score_threshold",),
    "segment_model_performance": ("score_threshold", "segment_family", "segment_name"),
    "report_narrative": ("page_order",),
    "quality_contract": ("object_name",),
    "report_readiness": ("check_id",),
}


def digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def canonical(value: Any) -> Any:
    """Tag types, preserving booleans, null and text while rounding numeric precision."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, int | float | decimal.Decimal):
        try:
            amount = decimal.Decimal(str(value))
            if not amount.is_finite():
                return ("nonfinite", str(value))
            return ("number", format(amount.quantize(PRECISION, rounding=decimal.ROUND_HALF_EVEN), "f"))
        except decimal.InvalidOperation:
            return ("nonfinite", str(value))
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, list):
        return ("array", tuple(canonical(item) for item in value))
    if isinstance(value, dict):
        return ("object", tuple((key, canonical(value[key])) for key in sorted(value)))
    raise TypeError("Unsupported JSON cell type")


def row_counter(rows: list[dict[str, Any]]) -> Counter[Any]:
    return Counter(canonical(row) for row in rows)


def schema_of(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({key for row in rows for key in row})


def indexed_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[Any, dict[str, Any]] | None:
    index = {}
    for row in rows:
        if not all(key in row for key in keys):
            return None
        identity = tuple(canonical(row[key]) for key in keys)
        if identity in index:
            return None
        index[identity] = row
    return index


def compare_group(
    name: str, historical: list[dict[str, Any]], current: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare all rows, ignoring order and sub-micro numeric noise."""
    old_schema, new_schema = schema_of(historical), schema_of(current)
    removed = sorted(set(old_schema) - set(new_schema))
    added = sorted(set(new_schema) - set(old_schema))
    historic_counter, current_counter = row_counter(historical), row_counter(current)
    removed_rows = sum((historic_counter - current_counter).values())
    added_rows = sum((current_counter - historic_counter).values())
    result: dict[str, Any] = {
        "status": "MATCH" if not removed and not added and historic_counter == current_counter else "DIFF",
        "historical_rows": len(historical),
        "current_rows": len(current),
        "missing_fields_in_current": removed,
        "new_fields_in_current": added,
        "historical_only_rows": removed_rows,
        "current_only_rows": added_rows,
        "changed_field_counts": {},
        "examples": [],
    }
    if result["status"] == "MATCH":
        return result

    key_fields = KEYS[name]
    old_index = indexed_rows(historical, key_fields)
    new_index = indexed_rows(current, key_fields)
    if old_index is None or new_index is None:
        result["match_basis"] = "full_row_multiset_only_duplicate_or_missing_keys"
        return result
    result["match_basis"] = "unique_natural_key_and_full_row_multiset"
    old_keys, new_keys = set(old_index), set(new_index)
    result["historical_only_keys"] = len(old_keys - new_keys)
    result["current_only_keys"] = len(new_keys - old_keys)
    changes: dict[str, int] = defaultdict(int)
    examples: list[dict[str, str]] = []
    for identity in sorted(old_keys & new_keys, key=repr):
        left, right = old_index[identity], new_index[identity]
        for field in sorted(set(left) | set(right)):
            if field not in left or field not in right:
                continue  # Already accounted for by schema or row set differences.
            if canonical(left[field]) != canonical(right[field]):
                changes[field] += 1
                if len(examples) < MAX_EXAMPLES:
                    examples.append({
                        "key_sha256": digest(identity)[:16],
                        "field": field,
                        "historical_sha256": digest(left[field])[:16],
                        "current_sha256": digest(right[field])[:16],
                    })
    result["changed_field_counts"] = dict(sorted(changes.items()))
    result["examples"] = examples
    return result


def audit(snapshot: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValueError("Snapshot must be a JSON object")
    if current is not None and not isinstance(current, dict):
        raise ValueError("Current evidence must be a JSON object")
    groups: dict[str, dict[str, Any]] = {}
    for name, source in SOURCES.items():
        old = snapshot.get(name)
        new = None if current is None else current.get(name)
        row: dict[str, Any] = {
            "source_table": source,
            "query_shape": SOURCE_SHAPE.get(name, "direct"),
            "source_table_shared": source == "fact_train_transactions",
        }
        if not isinstance(old, list) or any(not isinstance(item, dict) for item in old):
            row["status"] = "INVALID_HISTORICAL"
        elif current is None:
            row.update(status="NOT_CHECKED", historical_rows=len(old))
        elif not isinstance(new, list) or any(not isinstance(item, dict) for item in new):
            row.update(status="MISSING_CURRENT", historical_rows=len(old))
        else:
            row.update(compare_group(name, old, new))
        groups[name] = row
    summary = Counter(group["status"] for group in groups.values())
    meta_old = snapshot.get("meta") if isinstance(snapshot.get("meta"), dict) else {}
    meta_new = current.get("meta") if current and isinstance(current.get("meta"), dict) else {}
    metadata_fields = ("project_id", "dataset", "total_transactions", "fraud_transactions")
    meta_differences = [field for field in metadata_fields if current is not None and (
        field not in meta_new or canonical(meta_old.get(field)) != canonical(meta_new.get(field))
    )]
    if current is None:
        overall = "NOT_RUN"
    elif summary["INVALID_HISTORICAL"] or summary["MISSING_CURRENT"]:
        overall = "INCOMPLETE"
    elif summary["DIFF"] or meta_differences:
        overall = "DIFF"
    else:
        overall = "STRUCTURAL_MATCH"
    same_rows = current is not None and digest({k: snapshot.get(k) for k in SOURCES}) == digest(
        {k: current.get(k) for k in SOURCES}
    )
    snapshot_names = set(snapshot) - {"meta"}
    current_names = set(current) - {"meta"} if current is not None else set()
    return {
        "audit_version": 1,
        "comparison_status": overall,
        "provenance_verdict": "UNVERIFIED_EXTERNAL_SOURCE",
        "source_query_jobs_executed": 0,
        "snapshot_sha256": digest(snapshot),
        "current_payload_sha256": digest(current) if current is not None else None,
        "same_published_payload": same_rows,
        "historical_snapshot_refresh": meta_old.get("refreshed_at"),
        "current_payload_refresh_claim": meta_new.get("refreshed_at"),
        "historical_project": meta_old.get("project_id"),
        "historical_dataset": meta_old.get("dataset"),
        "current_project": meta_new.get("project_id"),
        "current_dataset": meta_new.get("dataset"),
        "metadata_mismatch_fields": meta_differences,
        "reporting_group_count": len(SOURCES),
        "unique_physical_table_references": len(set(SOURCES.values())),
        "duplicate_fact_groups": sorted(name for name, table in SOURCES.items()
                                        if table == "fact_train_transactions"),
        "extra_historical_groups": sorted(snapshot_names - set(SOURCES)),
        "extra_current_groups": sorted(current_names - set(SOURCES)),
        "status_counts": dict(sorted(summary.items())),
        "groups": groups,
        "warning": (
            "Structural JSON comparison only. Current payload provenance, source lineage, "
            "BigQuery run status, real freshness and authorization are NOT established. "
            "Identical values or timestamps alone do not authorize snapshot replacement."
        ),
    }


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected a top-level JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH)
    parser.add_argument("--current-json", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        result = audit(
            read_json(args.snapshot),
            read_json(args.current_json) if args.current_json is not None else None,
        )
    except (OSError, ValueError, TypeError) as exc:
        # Never include private absolute paths, source data or credential strings.
        print(f"Snapshot audit could not run ({type(exc).__name__})", file=sys.stderr)
        return 2
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)
    # No external comparator is not a passing parity audit.
    return 0 if result["comparison_status"] == "STRUCTURAL_MATCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
