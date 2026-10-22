"""Reconcile all 27 public groups with bounded BigQuery tabledata and local SQL.

The explicit fact-read mode reads selected reporting dimensions into in-memory
DuckDB, never writes raw records, submits no cloud SQL jobs and leaves published
snapshots untouched. Presentation normalization is part of the public contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.audit_reporting_snapshot import (
    KEYS,
    SNAPSHOT_PATH,
    SOURCES,
    canonical,
    compare_group,
    indexed_rows,
    read_json,
)
from scripts.verify_reporting_tables_bigquery_readonly import DEFAULT_DATASET, DEFAULT_PROJECT, normalized_value

FACT_TABLE = "fact_train_transactions"
MAX_FACT_ROWS = 590_540
MAX_REPORT_ROWS = 10_000
FACT_FIELDS = (
    "product_cd", "amount_band", "card_network", "card_type", "purchaser_email_group",
    "has_identity", "risk_band", "device_type", "transaction_amount", "is_fraud",
    "address_proxy_status", "distance_proxy_band",
)
SQL_TYPES = {
    "STRING": "VARCHAR", "INTEGER": "BIGINT", "INT64": "BIGINT",
    "FLOAT": "DOUBLE", "FLOAT64": "DOUBLE", "BOOLEAN": "BOOLEAN", "BOOL": "BOOLEAN",
    "NUMERIC": "DECIMAL(38,9)", "DECIMAL": "DECIMAL(38,9)", "DATE": "DATE",
    "DATETIME": "TIMESTAMP", "TIMESTAMP": "TIMESTAMPTZ", "TIME": "TIME",
}


def quoted(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
        raise ValueError("Unsupported source identifier")
    return f'"{name}"'


def table_signature(info: Any) -> tuple[Any, ...]:
    return (info.etag, info.num_rows, str(info.modified), tuple(
        (col.name, col.field_type, col.mode) for col in info.schema
    ))


def mirror_table(client: Any, connection: Any, table_ref: str, *, fact: bool) -> dict[str, Any]:
    """Read bounded API pages to an in-memory table with schema and change guards."""
    import pandas as pd

    info = client.get_table(table_ref, timeout=30)
    table = table_ref.rsplit(".", 1)[-1]
    cap = MAX_FACT_ROWS if fact else MAX_REPORT_ROWS
    count = info.num_rows
    if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= cap:
        raise ValueError("Source table row count exceeds explicit read bound")
    if fact and count != MAX_FACT_ROWS:
        raise ValueError("Fact population does not match the full historical portfolio")
    schema = [col for col in info.schema if not fact or col.name in FACT_FIELDS]
    if fact and {col.name for col in schema} != set(FACT_FIELDS):
        raise ValueError("Required reporting dimensions are absent from fact source")
    if not schema or any(col.mode == "REPEATED" or col.field_type not in SQL_TYPES for col in schema):
        raise ValueError("Unsupported source schema")
    names = [col.name for col in schema]
    definition = ", ".join(f"{quoted(col.name)} {SQL_TYPES[col.field_type]}" for col in schema)
    connection.execute(f"create table {quoted(table)} ({definition})")
    iterator = client.list_rows(info, selected_fields=schema, max_results=count + 1, page_size=10_000, timeout=60)
    seen = 0
    # Sum of row digests is order independent and retains duplicate multiplicity.
    fingerprint_sum = 0
    modulus = 1 << 256
    for page in iterator.pages:
        batch = []
        for row in page:
            record = {name: normalized_value(row[name]) for name in names}
            hashed = hashlib.sha256(json.dumps(record, sort_keys=True, default=str, separators=(",", ":")).encode()).digest()
            fingerprint_sum = (fingerprint_sum + int.from_bytes(hashed, "big")) % modulus
            batch.append(record)
        seen += len(batch)
        if seen > count:
            raise ValueError("Source grew during bounded read")
        if batch:
            connection.register("_source_page", pd.DataFrame(batch, columns=names))
            columns = ", ".join(quoted(name) for name in names)
            connection.execute(f"insert into {quoted(table)} select {columns} from _source_page")
            connection.unregister("_source_page")
    if seen != count:
        raise ValueError("Source read incomplete")
    after = client.get_table(table_ref, timeout=30)
    if table_signature(info) != table_signature(after):
        raise ValueError("Source metadata changed during read")
    return {
        "rows_read": seen,
        "field_names": names,
        "source_modified_at": info.modified.isoformat() if info.modified else None,
        "source_etag_sha256": hashlib.sha256(str(info.etag).encode()).hexdigest(),
        "schema_sha256": hashlib.sha256(str(table_signature(info)[3]).encode()).hexdigest(),
        "selected_row_multiset_sha256_sum_mod_2_256": f"{fingerprint_sum:064x}",
        "fingerprint_definition": "SHA-256 per canonical selected row; sum modulo 2^256, duplicate multiplicity retained",
        "_signature": table_signature(info),
    }


def public_query_rows(connection: Any, group: str) -> list[dict[str, Any]]:
    """Execute one exact application query against the selected local mirror."""
    from webapp.main import TABLE_QUERIES, normalize_public_row

    sql = TABLE_QUERIES[group].format(table=quoted(SOURCES[group]))
    cursor = connection.execute(sql)
    fields = [column[0] for column in cursor.description]
    return [normalize_public_row(group, dict(zip(fields, row, strict=True))) for row in cursor.fetchall()]


def evaluate_groups(connection: Any, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Use the application's exact query strings, including all filters/limits."""
    from webapp.main import TABLE_QUERIES

    results = {}
    for group, table in SOURCES.items():
        rows = public_query_rows(connection, group)
        expected = snapshot.get(group)
        if not isinstance(expected, list) or any(not isinstance(row, dict) for row in expected):
            raise ValueError("Historical group is absent or malformed")
        comparison = compare_group(group, expected, rows)
        if comparison["status"] == "DIFF":
            residuals = floating_aggregation_residuals(group, expected, rows)
            if residuals is not None:
                comparison["strict_comparison_status"] = "DIFF"
                comparison["status"] = "MATCH_WITH_FLOAT_AGGREGATION_TOLERANCE"
                comparison["floating_aggregation_diagnostic"] = residuals
        results[group] = {
            "source_table": table,
            "query_sha256": hashlib.sha256(TABLE_QUERIES[group].encode()).hexdigest(),
            "public_normalization_applied": True,
            **comparison,
        }
    return results


def floating_aggregation_residuals(
    group: str, expected: list[dict[str, Any]], current: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Explain only tiny floating residuals; keys, counts, text and nulls stay strict.

    Six-decimal quantization can straddle a rounding boundary for two essentially
    identical binary floating averages. Preserve the strict diff and report this
    separate, much tighter absolute/relative tolerance explicitly.
    """
    keys = KEYS.get(group)
    if not keys or len(expected) != len(current):
        return None
    left, right = indexed_rows(expected, keys), indexed_rows(current, keys)
    if left is None or right is None or left.keys() != right.keys():
        return None
    count, maximum = 0, 0.0
    for key, row in left.items():
        other = right[key]
        if row.keys() != other.keys():
            return None
        for field, a in row.items():
            b = other[field]
            if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
                if a != b or type(a) is not type(b):
                    return None
            elif isinstance(a, int | float | Decimal) and isinstance(b, int | float | Decimal):
                if isinstance(a, int) and isinstance(b, int):
                    if a != b:
                        return None
                elif not (math.isfinite(float(a)) and math.isfinite(float(b))
                          and math.isclose(float(a), float(b), abs_tol=1e-9, rel_tol=1e-12)):
                    return None
                delta = abs(float(a) - float(b))
                maximum = max(maximum, delta)
                count += delta > 0
            elif canonical(a) != canonical(b):
                return None
    return {"absolute_tolerance": 1e-9, "relative_tolerance": 1e-12,
            "maximum_absolute_residual": maximum, "numeric_cells_with_nonzero_residual": count,
            "integer_counts_text_nulls_and_natural_keys": "strict"}


def inspect(client: Any, snapshot: dict[str, Any]) -> dict[str, Any]:
    import duckdb

    meta = snapshot.get("meta", {})
    if meta.get("project_id") != DEFAULT_PROJECT or meta.get("dataset") != DEFAULT_DATASET:
        raise ValueError("Only the committed authorized source is supported")
    prefix = f"{DEFAULT_PROJECT}.{DEFAULT_DATASET}"
    if client.get_dataset(prefix, timeout=30).location != "US":
        raise ValueError("Authorized dataset region must be US")
    if meta.get("total_transactions") != MAX_FACT_ROWS:
        raise ValueError("Historical portfolio count does not match explicit fact bound")
    physical = {entry.table_id for entry in client.list_tables(prefix, timeout=30)}
    required = set(SOURCES.values())
    if not required <= physical:
        raise ValueError("Some expected physical sources are missing")
    sources = {}
    with duckdb.connect(":memory:") as connection:
        connection.execute("set threads=2")
        for table in sorted(required):
            sources[table] = mirror_table(client, connection, f"{prefix}.{table}", fact=table == FACT_TABLE)
        groups = evaluate_groups(connection, snapshot)
        # All source tables must remain unchanged through the complete audit.
        for table, evidence in sources.items():
            latest = client.get_table(f"{prefix}.{table}", timeout=30)
            if evidence.pop("_signature") != table_signature(latest):
                raise ValueError("Source changed across the complete audit interval")
    statuses = Counter(item["status"] for item in groups.values())
    success = len(groups) == 27 and set(statuses) <= {"MATCH", "MATCH_WITH_FLOAT_AGGREGATION_TOLERANCE"}
    return {
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "mode": "FULL_PUBLIC_CONTRACT_BIGQUERY_TABLEDATA_LOCAL_SQL",
        "status": "MATCH_ALL_27_PUBLIC_GROUPS" if success else "PUBLIC_GROUP_DIFFERENCES",
        "verified_full_27_group_parity": success,
        "project": DEFAULT_PROJECT, "dataset": DEFAULT_DATASET, "region": "US",
        "sql_query_jobs_submitted": 0,
        "cloud_writes": 0, "raw_source_records_written": False,
        "fact_selected_rows_read": sources[FACT_TABLE]["rows_read"],
        "fact_read_bound": MAX_FACT_ROWS, "report_table_read_bound": MAX_REPORT_ROWS,
        "source_table_count": len(sources), "report_groups": len(groups),
        "historical_refresh_unchanged": meta.get("refreshed_at"), "snapshot_rewritten": False,
        "snapshot_canonical_sha256": hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "verifier_source_sha256": hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "status_counts": dict(statuses), "groups": groups, "sources": sources,
        "scope": "Selected source columns transformed by exact public query/normalization contracts. No raw-table byte equality, source rebuild, new model calibration or freshness beyond this observation is implied.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--credentials-file", type=Path)
    auth.add_argument("--use-adc", action="store_true")
    parser.add_argument("--allow-bounded-fact-read", action="store_true", required=True,
                        help="Explicitly authorize 590540 selected fact rows into memory; zero cloud SQL")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        from google.cloud import bigquery

        scopes = ["https://www.googleapis.com/auth/bigquery.readonly"]
        if args.use_adc:
            import google.auth
            credentials, _ = google.auth.default(scopes=scopes)
        else:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(str(args.credentials_file), scopes=scopes)
        client = bigquery.Client(project=DEFAULT_PROJECT, credentials=credentials)
        result = inspect(client, read_json(args.snapshot))
    except Exception as exc:
        print(f"Full read-only reconciliation unavailable ({type(exc).__name__})", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "status_counts", "source_table_count", "fact_selected_rows_read")}))
    return 0 if result["verified_full_27_group_parity"] else 1


if __name__ == "__main__":
    sys.exit(main())
