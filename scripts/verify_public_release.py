"""F08 independent public production smoke: read-only HTTP with commit attestation.

Checks exactly the approved production hostname. Does not carry credentials,
follow redirects, query BigQuery, trigger a deployment or modify the model.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from scripts.verify_snapshot_release import verify_payloads

PRODUCTION_HOST = "fraud-project-web.vercel.app"
MAX_BYTES = 16_000_000


class NoRedirect(HTTPRedirectHandler):
    """Treat access-control redirects as unavailable, not a successful page."""

    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        del req, fp, code, msg, headers, newurl
        return None


def _get(path: str) -> bytes:
    if path not in {"/", "/studio", "/api/evidence-status", "/api/dashboard"}:
        raise ValueError("Unsupported public verification endpoint")
    opener = build_opener(NoRedirect)
    request = Request("https://" + PRODUCTION_HOST + path, headers={"Accept": "application/json,text/html"})
    with opener.open(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError("Non-200 public response")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Remote response exceeds size guard")
        return data


def evaluate_public_release(
    expected_sha: str,
    evidence: dict[str, Any],
    dashboard: dict[str, Any],
    report_html: str,
    studio_html: str,
) -> dict[str, Any]:
    """Fail unless same approved commit, dated source and both real UI routes."""
    if not re.fullmatch(r"[a-fA-F0-9]{40}", expected_sha):
        raise ValueError("Expected commit must be a full hexadecimal Git SHA")
    summary = verify_payloads(evidence, dashboard, report_html)
    errors = list(summary["checks_failed"])
    build_sha = evidence.get("deployed_git_commit")
    if not isinstance(build_sha, str) or not re.fullmatch(r"[a-fA-F0-9]{40}", build_sha):
        errors.append("Production build SHA is not attested by server runtime")
    elif build_sha.lower() != expected_sha.lower():
        errors.append("Production build SHA does not match target git revision")
    if 'id="historical-review-queue"' not in studio_html:
        errors.append("Live Decision Studio does not expose historical review queue")
    if 'id="selected-detail"' not in studio_html:
        errors.append("Live Decision Studio lacks verified chart selection panel")
    if 'id="studio-evidence-source"' not in studio_html:
        errors.append("Live Decision Studio lacks source trust disclosure")
    if 'href="/studio?view=overview"' not in report_html:
        errors.append("Live dashboard has no accessible Decision Studio navigation")
    return {
        "result": "PASS_PUBLIC_HISTORICAL_RELEASE" if not errors else "FAIL_PUBLIC_RELEASE",
        "expected_git_sha": expected_sha.lower(),
        "observed_git_sha": build_sha if isinstance(build_sha, str) and re.fullmatch(r"[a-fA-F0-9]{40}", build_sha) else None,
        "historical_snapshot_as_of": evidence.get("source_as_of"),
        "verified_live_bigquery": False,
        "verified_model_calibration": False,
        "verified_payment_processing": False,
        "checked_hostname": PRODUCTION_HOST,
        "checks_failed": errors,
    }


def inspect_public_release(expected_sha: str) -> dict[str, Any]:
    """Network calls only to fixed allowlisted domain, without auth material."""
    try:
        evidence = json.loads(_get("/api/evidence-status"))
        # Fail quickly on un-attested old prod before fetching the whole dataset.
        sha = evidence.get("deployed_git_commit")
        if sha is None or str(sha).lower() != expected_sha.lower():
            return {
                "result": "FAIL_PUBLIC_RELEASE",
                "expected_git_sha": expected_sha.lower(),
                "observed_git_sha": sha if isinstance(sha, str) and re.fullmatch(r"[a-fA-F0-9]{40}", sha) else None,
                "checked_hostname": PRODUCTION_HOST,
                "checks_failed": ["Production build SHA absent or does not match target commit"],
            }
        dashboard = json.loads(_get("/api/dashboard"))
        html = _get("/").decode("utf-8")
        studio = _get("/studio").decode("utf-8")
        return evaluate_public_release(expected_sha, evidence, dashboard, html, studio)
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, UnicodeError, TypeError):
        return {
            "result": "FAIL_PUBLIC_RELEASE",
            "expected_git_sha": expected_sha.lower(),
            "checked_hostname": PRODUCTION_HOST,
            "checks_failed": ["Public HTTP endpoint unavailable, protected or malformed; no production pass claimed"],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True, help="Exact reviewed 40-character Git revision")
    parser.add_argument("--attempts", type=int, default=1, help="Bounded attempts for deployment propagation")
    parser.add_argument("--delay-seconds", type=int, default=8)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-fA-F0-9]{40}", args.expected_sha):
        parser.error("--expected-sha requires a full hexadecimal Git revision")
    if not 1 <= args.attempts <= 20 or not 0 <= args.delay_seconds <= 30:
        parser.error("Attempts must be 1–20, delay must be 0–30 seconds")
    report: dict[str, Any] = {}
    for attempt in range(args.attempts):
        report = inspect_public_release(args.expected_sha)
        if report["result"] == "PASS_PUBLIC_HISTORICAL_RELEASE":
            break
        if attempt + 1 < args.attempts:
            time.sleep(args.delay_seconds)
    report["attempts_executed"] = attempt + 1
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["result"] == "PASS_PUBLIC_HISTORICAL_RELEASE" else 1


if __name__ == "__main__":
    sys.exit(main())
