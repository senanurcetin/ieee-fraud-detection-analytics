"""Offline, independent arithmetic checks for the published Fraud snapshot.

Run without BigQuery, credentials, paid CI or access to private Kaggle files.
These are holdout consistency checks, not a substitute for source-data
lineage, future production drift monitoring or data refresh.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = json.loads(
    (ROOT / "webapp" / "snapshots" / "dashboard.json").read_text(encoding="utf-8")
)


def test_snapshot_is_dated_and_provenance_is_explicit():
    metadata = SNAPSHOT["meta"]
    assert metadata["backend"] == "snapshot"
    assert metadata["source_backend"] == "bigquery"
    assert metadata["refreshed_at"]
    timestamp = datetime.fromisoformat(metadata["refreshed_at"].replace("Z", "+00:00"))
    assert timestamp <= datetime.now(UTC)
    assert metadata["table_count"] >= 25


def test_portfolio_and_amount_band_denominators_reconcile():
    kpi = SNAPSHOT["executive_kpis"][0]
    assert kpi["total_transactions"] == (
        kpi["fraud_transactions"] + kpi["legitimate_transactions"]
    )
    assert math.isclose(
        kpi["fraud_rate"],
        kpi["fraud_transactions"] / kpi["total_transactions"],
        abs_tol=1e-11,
    )
    amount = SNAPSHOT["amount_bands"]
    assert sum(row["transaction_count"] for row in amount) == kpi["total_transactions"]
    assert sum(row["fraud_count"] for row in amount) == kpi["fraud_transactions"]
    for row in amount:
        assert math.isclose(
            row["fraud_rate"], row["fraud_count"] / row["transaction_count"],
            abs_tol=1e-11,
        )


def test_validation_threshold_confusion_and_workload_reconcile():
    thresholds = SNAPSHOT["validation_threshold_simulation"]
    assert thresholds
    calibration = SNAPSHOT["model_calibration"]
    holdout_n = sum(row["transaction_count"] for row in calibration)
    holdout_fraud = sum(
        row["transaction_count"] * row["observed_fraud_rate"] for row in calibration
    )
    total_positives = round(holdout_fraud)
    assert all(row["evidence_scope"] == "validation_holdout" for row in thresholds)
    previous = None
    for row in thresholds:
        reviewed = row["review_count"]
        captured = row["captured_fraud_count"]
        false_positive = row["false_positive_count"]
        false_negative = row["false_negative_count"]
        assert reviewed == captured + false_positive
        assert captured + false_negative == total_positives
        assert 0 <= reviewed <= holdout_n
        assert math.isclose(
            row["precision_rate"], captured / reviewed if reviewed else 0,
            abs_tol=1e-10,
        )
        assert math.isclose(row["fraud_capture_rate"], captured / total_positives, abs_tol=1e-10)
        assert math.isclose(row["workload_share"], reviewed / holdout_n, abs_tol=1e-10)
        assert math.isclose(
            row["false_positive_rate"],
            false_positive / (holdout_n - total_positives),
            abs_tol=1e-10,
        )
        if previous is not None:
            assert row["score_threshold"] >= previous["score_threshold"]
            assert reviewed <= previous["review_count"]
            assert captured <= previous["captured_fraud_count"]
        previous = row


def test_holdout_calibration_ece_and_brier_warning_are_grounded():
    calibration = SNAPSHOT["model_calibration"]
    n = sum(row["transaction_count"] for row in calibration)
    ref = calibration[0]
    ece = sum(
        row["transaction_count"] * abs(
            row["mean_predicted_probability"] - row["observed_fraud_rate"]
        )
        for row in calibration
    ) / n
    assert math.isclose(ece, ref["expected_calibration_error"], abs_tol=1e-10)
    assert math.isclose(
        sum(row["transaction_count"] * row["observed_fraud_rate"] for row in calibration)
        / n,
        ref["holdout_baseline_rate"],
        abs_tol=1e-10,
    )
    for row in calibration:
        assert math.isclose(
            row["calibration_gap"],
            row["mean_predicted_probability"] - row["observed_fraud_rate"],
            abs_tol=1e-10,
        )
    assert ref["brier_score"] > ref["baseline_brier_score"]
    ui = (ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    assert "Calibration warning" in ui
    assert "sparsely sampled polylines" in ui
    assert "Illustrative Missed Amount" in ui


def test_holdout_risk_bands_reconcile():
    rows = SNAPSHOT["validation_risk_bands"]
    assert rows
    holdout_n = sum(row["transaction_count"] for row in SNAPSHOT["model_calibration"])
    positives = round(sum(
        row["transaction_count"] * row["observed_fraud_rate"]
        for row in SNAPSHOT["model_calibration"]
    ))
    assert sum(row["transaction_count"] for row in rows) == holdout_n
    assert sum(row["observed_fraud_count"] for row in rows) == positives
    for row in rows:
        assert math.isclose(
            row["observed_fraud_rate"],
            row["observed_fraud_count"] / row["transaction_count"],
            abs_tol=1e-11,
        )


def test_no_invented_action_score_in_drill():
    ui = (ROOT / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    assert "OBSERVED EVIDENCE / NOT AN ACTION SCORE" in ui
    assert "No synthetic priority points" in ui
    assert "label:'Action heuristic'" not in ui
