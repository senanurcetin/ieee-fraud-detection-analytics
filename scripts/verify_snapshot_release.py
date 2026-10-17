"""Fail-closed local snapshot-demo smoke test; not a live fraud release gate.

Usage:
    python -m scripts.verify_snapshot_release --base-url http://127.0.0.1:8000
No BigQuery credentials or payment network access are required.
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def verify_payloads(evidence: dict, dashboard: dict, html: str) -> dict:
    """Check source integrity and explicit historical/trust disclosures."""
    errors: list[str] = []
    meta = dashboard.get("meta", {}) if isinstance(dashboard, dict) else {}
    groups = {k: v for k, v in dashboard.items() if k != "meta"} if isinstance(dashboard, dict) else {}
    if len(groups) != 27 or not all(isinstance(value, list) for value in groups.values()):
        errors.append("Expected 27 populated-format reporting groups")
    if meta.get("total_transactions") != 590540:
        errors.append("Historical transaction population mismatch")
    if meta.get("fraud_transactions") != 20663:
        errors.append("Historical observed fraud count mismatch")
    if evidence.get("source_as_of") != meta.get("refreshed_at"):
        errors.append("Evidence snapshot timestamp does not match dashboard")
    if evidence.get("source_status") not in {"historical_dated", "historical_over_30d"}:
        errors.append("Source is not properly identified as a dated historical snapshot")
    if evidence.get("source_parity") != "not_verified_against_current_bigquery":
        errors.append("Current BigQuery parity must remain unverified without source comparison")
    if evidence.get("report_groups") != 27 or evidence.get("physical_source_tables") != 24:
        errors.append("Snapshot/report-table mapping mismatch")
    if evidence.get("live_transaction_monitoring") is not False:
        errors.append("No live transaction monitoring evidence is available")
    if evidence.get("production_model_evidence") is not False:
        errors.append("No validated live model serving evidence is available")
    if "uncalibrated" not in evidence.get("model_output_contract", ""):
        errors.append("Current model-score calibration disclaimer absent")
    if "nexus-evidence-context" not in html or "NEXUS" not in html:
        errors.append("NEXUS historical provenance rail is missing from the served HTML")
    return {
        "result": "PASS_HISTORICAL_OFFLINE_DEMO" if not errors else "FAIL_RELEASE_SMOKE",
        "model_promoted": False,
        "live_data_verified": False,
        "bigquery_parity_verified": False,
        "production_deployed": False,
        "source_as_of": evidence.get("source_as_of"),
        "checks_failed": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--allow-remote", action="store_true", help="Explicitly allow non-loopback hosts")
    args = parser.parse_args(argv)
    parsed = urlsplit(args.base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        parser.error("Expected a plain HTTP(S) origin, no credentials or URL queries")
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} and not args.allow_remote:
        parser.error("External hosts require --allow-remote; default is local-only")
    origin = args.base_url.rstrip("/")
    try:
        def get(path: str) -> bytes:
            with urlopen(origin + path, timeout=8) as response:
                if response.status != 200:
                    raise ValueError("Unexpected HTTP status")
                content = response.read(16_000_001)
                if len(content) > 16_000_000:
                    raise ValueError("Response exceeds bounded smoke-test size")
                return content

        evidence = json.loads(get("/api/evidence-status"))
        dashboard = json.loads(get("/api/dashboard"))
        html = get("/").decode("utf-8")
        report = verify_payloads(evidence, dashboard, html)
    except (OSError, URLError, ValueError, UnicodeError, json.JSONDecodeError):
        report = {
            "result": "FAIL_RELEASE_SMOKE",
            "model_promoted": False,
            "live_data_verified": False,
            "bigquery_parity_verified": False,
            "production_deployed": False,
            "checks_failed": ["Local endpoint unavailable, invalid or inconsistent"],
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result"] == "PASS_HISTORICAL_OFFLINE_DEMO" else 1


if __name__ == "__main__":
    sys.exit(main())
