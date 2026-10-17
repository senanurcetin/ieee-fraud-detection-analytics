"""F06: create a redacted, offline fraud score-shift report from two CSV cohorts.

Samples must be strictly time-ordered in relative IEEE-CIS TransactionDT.
No labels are loaded, model training, credentials, network or BigQuery jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

from src.drift_monitoring import DriftPolicy, compare_historical_score_windows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_cohort(path: Path, score_col: str, time_col: str, features: list[str]) -> pd.DataFrame:
    """Load an explicit allowlist, never fraud labels or free-form attributes."""
    header = list(pd.read_csv(path, nrows=0).columns)
    mandatory = {score_col, time_col}
    if not mandatory.issubset(header):
        raise ValueError("Required scoring or elapsed-time column not present")
    allowed = mandatory | set(features)
    return pd.read_csv(path, usecols=lambda column: column in allowed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="Earlier scored historical cohort")
    parser.add_argument("--observed", type=Path, required=True, help="Later scored historical cohort")
    parser.add_argument("--output", type=Path, default=Path("outputs/research/fraud_offline_drift.json"))
    parser.add_argument("--score-column", default="predicted_fraud_probability")
    parser.add_argument("--time-column", default="TransactionDT")
    parser.add_argument("--feature", action="append", default=[], help="Compare missingness for this feature")
    parser.add_argument("--min-rows", type=int, default=200)
    args = parser.parse_args(argv)
    if args.min_rows < 1:
        parser.error("--min-rows must be positive")
    try:
        earlier = read_cohort(args.reference, args.score_column, args.time_column, args.feature)
        later = read_cohort(args.observed, args.score_column, args.time_column, args.feature)
        report = compare_historical_score_windows(
            earlier,
            later,
            score_col=args.score_column,
            time_col=args.time_column,
            features=args.feature,
            policy=DriftPolicy(
                min_reference_rows=args.min_rows,
                min_observed_rows=args.min_rows,
            ),
        )
        report["source_digests"] = {
            "reference_sha256": sha256_file(args.reference),
            "observed_sha256": sha256_file(args.observed),
        }
        report["paths_logged"] = False
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        # Do not expose local filenames, row values or authentication material.
        print(f"Offline drift report unavailable ({type(exc).__name__})", file=sys.stderr)
        return 2
    result = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Offline evidence report written. Status: {report['status']}. No model changed.")
    return 0 if report["status"] == "NO_POLICY_FLAG" else 1


if __name__ == "__main__":
    raise SystemExit(main())
