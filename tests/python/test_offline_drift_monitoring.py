"""F06 offline drift regressions from synthetic cohorts only (no Kaggle/cloud)."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
monitor = importlib.import_module("src.drift_monitoring")
cli = importlib.import_module("scripts.audit_offline_drift")


def cohorts(n: int = 300, seed: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    score = rng.uniform(0, 1, size=n)
    ref = pd.DataFrame({
        "TransactionDT": np.arange(n) * 60,
        "predicted_fraud_probability": score,
        "V9": rng.normal(size=n),
    })
    later = pd.DataFrame({
        "TransactionDT": (np.arange(n) + n + 2) * 60,
        "predicted_fraud_probability": score.copy(),
        "V9": rng.normal(size=n),
    })
    return ref, later


def test_identical_distribution_is_stable_and_counts_all_rows() -> None:
    earlier, later = cohorts()
    report = monitor.compare_historical_score_windows(
        earlier, later, features=["V9"]
    )
    assert report["status"] == "NO_POLICY_FLAG"
    assert report["score_psi"] == pytest.approx(0, abs=1e-12)
    assert sum(b["reference_count"] for b in report["score_bins"]) == len(earlier)
    assert sum(b["observed_count"] for b in report["score_bins"]) == len(later)
    assert report["labels_accessed"] is False
    assert report["model_modified"] is False
    assert report["real_time_evidence"] is False
    assert report["score_summary"]["reference_mean"] == pytest.approx(
        report["score_summary"]["observed_mean"]
    )


def test_large_score_distribution_shift_is_flagged_but_not_retraining() -> None:
    earlier, later = cohorts()
    later["predicted_fraud_probability"] = np.linspace(0.94, 1.0, len(later))
    report = monitor.compare_historical_score_windows(earlier, later)
    assert report["status"] == "INVESTIGATE_SHIFT"
    assert report["score_psi"] > 0.25
    assert "Do not automatically retrain" in report["operator_action"]


def test_only_missingness_delta_can_trigger_review() -> None:
    earlier, later = cohorts()
    later.loc[:95, "V9"] = np.nan
    report = monitor.compare_historical_score_windows(
        earlier, later, features=["V9"]
    )
    assert report["status"] == "REVIEW_SHIFT"
    assert report["feature_missingness"][0]["status"] == "REVIEW"
    assert report["feature_missingness"][0]["absolute_missingness_change"] > 0.3


def test_missing_source_field_is_never_silent() -> None:
    earlier, later = cohorts()
    later = later.drop(columns=["V9"])
    report = monitor.compare_historical_score_windows(
        earlier, later, features=["V9"]
    )
    assert report["status"] == "SCHEMA_REVIEW_REQUIRED"
    assert report["feature_missingness"][0]["status"] == "SCHEMA_MISSING"


def test_overlapping_periods_or_missing_elapsed_times_rejected() -> None:
    earlier, later = cohorts()
    later.loc[0, "TransactionDT"] = earlier["TransactionDT"].max()
    with pytest.raises(ValueError, match="strictly chronological"):
        monitor.compare_historical_score_windows(earlier, later)
    later = later.drop(columns=["TransactionDT"])
    with pytest.raises(ValueError):
        monitor.compare_historical_score_windows(earlier, later)


@pytest.mark.parametrize("bad", (-0.1, 1.1, np.nan, np.inf))
def test_invalid_or_missing_score_is_rejected(bad: float) -> None:
    earlier, later = cohorts()
    later.loc[0, "predicted_fraud_probability"] = bad
    with pytest.raises(ValueError):
        monitor.compare_historical_score_windows(earlier, later)


def test_small_cohorts_do_not_claim_success() -> None:
    earlier, later = cohorts(n=20)
    report = monitor.compare_historical_score_windows(earlier, later)
    assert report["status"] == "INSUFFICIENT_SUPPORT"


def test_label_columns_cannot_be_monitored_as_features() -> None:
    earlier, later = cohorts()
    earlier["isFraud"] = 0
    later["isFraud"] = 1
    with pytest.raises(ValueError):
        monitor.compare_historical_score_windows(
            earlier, later, features=["isFraud"]
        )


def test_policy_input_is_checked() -> None:
    with pytest.raises(ValueError):
        monitor.DriftPolicy(psi_review=0.3, psi_investigate=0.2)
    with pytest.raises(ValueError):
        monitor.DriftPolicy(min_observed_rows=0)


def test_cli_reads_no_labels_and_records_real_file_digests(tmp_path: Path) -> None:
    earlier, later = cohorts()
    earlier["isFraud"] = 1
    later["isFraud"] = 0
    a, b = tmp_path / "reference.csv", tmp_path / "later.csv"
    earlier.to_csv(a, index=False)
    later.to_csv(b, index=False)
    permitted = cli.read_cohort(
        a, "predicted_fraud_probability", "TransactionDT", ["V9"]
    )
    assert "isFraud" not in permitted.columns
    outfile = tmp_path / "report.json"
    status = cli.main([
        "--reference", str(a),
        "--observed", str(b),
        "--output", str(outfile),
        "--feature", "V9",
    ])
    assert status == 0
    payload = json.loads(outfile.read_text(encoding="utf-8"))
    assert payload["status"] == "NO_POLICY_FLAG"
    assert payload["source_digests"]["reference_sha256"] == cli.sha256_file(a)
    assert payload["source_digests"]["observed_sha256"] == cli.sha256_file(b)
    assert payload["paths_logged"] is False
    assert "isFraud" not in json.dumps(payload)


def test_cli_nonzero_on_real_shift_and_disallows_paths_in_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    earlier, later = cohorts()
    later["predicted_fraud_probability"] = 0.99
    a, b = tmp_path / "reference.csv", tmp_path / "observed.csv"
    earlier.to_csv(a, index=False)
    later.to_csv(b, index=False)
    status = cli.main([
        "--reference", str(a),
        "--observed", str(b),
        "--output", str(tmp_path / "report.json"),
    ])
    assert status == 1
    assert "INVESTIGATE_SHIFT" in capsys.readouterr().out
    broken = cli.main([
        "--reference", str(tmp_path / "secret-source-does-not-exist.csv"),
        "--observed", str(b),
    ])
    assert broken == 2
    assert "secret-source" not in capsys.readouterr().err
