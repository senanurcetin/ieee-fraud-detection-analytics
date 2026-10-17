"""F06: deterministic offline distribution/coverage monitoring of historical fraud scores.

This is NOT a live fraud monitor, causal concept drift detector, or a measure
of fraud precision without validated later labels. It never trains a model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

SCORE_BINS: tuple[float, ...] = (0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 0.90, 1.0)
DISALLOWED_FEATURES = frozenset({
    "isFraud", "is_fraud", "actual_is_fraud", "observed_fraud_count",
    "fraud_count", "fraud_rate", "label", "target", "y",
})


@dataclass(frozen=True)
class DriftPolicy:
    """Monitor alert levels, not automatic deployment/retraining triggers."""

    psi_review: float = 0.10
    psi_investigate: float = 0.25
    missingness_change_review: float = 0.05
    min_reference_rows: int = 200
    min_observed_rows: int = 200

    def __post_init__(self) -> None:
        if not (0 < self.psi_review < self.psi_investigate):
            raise ValueError("PSI policy thresholds must increase")
        if not 0 < self.missingness_change_review <= 1:
            raise ValueError("Missingness limit must be between zero and one")
        if self.min_reference_rows < 1 or self.min_observed_rows < 1:
            raise ValueError("Sample minimums must be positive")


def _rank_scores(frame: pd.DataFrame, column: str) -> np.ndarray:
    if column not in frame or not len(frame):
        raise ValueError("Ranking score field missing or cohort empty")
    raw = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype="float64")
    if not np.isfinite(raw).all() or np.any((raw < 0) | (raw > 1)):
        raise ValueError("Missing/nonfinite/out-of-range ranking scores are not valid evidence")
    return raw


def _chronology(reference: pd.DataFrame, observed: pd.DataFrame, column: str) -> dict[str, float]:
    if column not in reference or column not in observed:
        raise ValueError("Both periods require elapsed-time TransactionDT")
    ref = pd.to_numeric(reference[column], errors="coerce").to_numpy(dtype="float64")
    obs = pd.to_numeric(observed[column], errors="coerce").to_numpy(dtype="float64")
    if not np.isfinite(ref).all() or not np.isfinite(obs).all():
        raise ValueError("Elapsed time contains invalid timestamps")
    if ref.max() >= obs.min():
        raise ValueError("Reference and observation time periods are not strictly chronological")
    return {
        "reference_min_dt": float(ref.min()),
        "reference_max_dt": float(ref.max()),
        "observed_min_dt": float(obs.min()),
        "observed_max_dt": float(obs.max()),
    }


def score_population_stability_index(
    reference_scores: np.ndarray, observed_scores: np.ndarray
) -> tuple[float, list[dict[str, float | int]]]:
    """PSI on predeclared [0,1] bins; additive smoothing handles empty bins."""
    reference_scores = np.asarray(reference_scores, dtype="float64")
    observed_scores = np.asarray(observed_scores, dtype="float64")
    if not len(reference_scores) or not len(observed_scores):
        raise ValueError("Both score samples must be present")
    for scores in (reference_scores, observed_scores):
        if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
            raise ValueError("Invalid probability-shaped ranking scores")

    hist_ref, _ = np.histogram(reference_scores, bins=SCORE_BINS)
    hist_observed, _ = np.histogram(observed_scores, bins=SCORE_BINS)
    # Jeffreys pseudocount is applied symmetrically and reported explicitly.
    n_bins = len(hist_ref)
    proportions_ref = (hist_ref + 0.5) / (len(reference_scores) + 0.5 * n_bins)
    proportions_observed = (hist_observed + 0.5) / (len(observed_scores) + 0.5 * n_bins)
    terms = (proportions_observed - proportions_ref) * np.log(
        proportions_observed / proportions_ref
    )
    bins = [
        {
            "lower_score_inclusive": float(SCORE_BINS[i]),
            "upper_score": float(SCORE_BINS[i + 1]),
            "reference_count": int(hist_ref[i]),
            "observed_count": int(hist_observed[i]),
            "reference_fraction_smoothed": float(proportions_ref[i]),
            "observed_fraction_smoothed": float(proportions_observed[i]),
            "psi_contribution": float(terms[i]),
        }
        for i in range(n_bins)
    ]
    return float(terms.sum()), bins


def compare_historical_score_windows(
    reference: pd.DataFrame,
    observed: pd.DataFrame,
    *,
    score_col: str = "predicted_fraud_probability",
    time_col: str = "TransactionDT",
    features: list[str] | None = None,
    policy: DriftPolicy | None = None,
) -> dict[str, Any]:
    """Evidence report with explicit train-before-observation chronology.

    Features include missingness only; labels and outcomes are never analyzed.
    """
    policy = policy or DriftPolicy()
    if score_col in DISALLOWED_FEATURES or time_col in DISALLOWED_FEATURES:
        raise ValueError("Labels/targets are never eligible as monitoring inputs")
    ref_scores = _rank_scores(reference, score_col)
    obs_scores = _rank_scores(observed, score_col)
    times = _chronology(reference, observed, time_col)
    requested = list(features or [])
    if len(requested) != len(set(requested)):
        raise ValueError("Monitoring feature names must be unique")
    if any(name in DISALLOWED_FEATURES or name in (score_col, time_col) for name in requested):
        raise ValueError("Labels, scoring and elapsed time cannot be feature coverage columns")
    psi, bins = score_population_stability_index(ref_scores, obs_scores)
    missingness = []
    for name in requested:
        if name not in reference or name not in observed:
            missingness.append({
                "feature": name,
                "status": "SCHEMA_MISSING",
                "reference_missing_fraction": (
                    float(reference[name].isna().mean()) if name in reference else None
                ),
                "observed_missing_fraction": (
                    float(observed[name].isna().mean()) if name in observed else None
                ),
                "absolute_missingness_change": None,
            })
            continue
        ref_missing = float(reference[name].isna().mean())
        obs_missing = float(observed[name].isna().mean())
        change = abs(obs_missing - ref_missing)
        missingness.append({
            "feature": name,
            "status": "REVIEW" if change >= policy.missingness_change_review else "WITHIN_POLICY",
            "reference_missing_fraction": ref_missing,
            "observed_missing_fraction": obs_missing,
            "absolute_missingness_change": change,
        })

    enough = len(reference) >= policy.min_reference_rows and len(observed) >= policy.min_observed_rows
    if not enough:
        status = "INSUFFICIENT_SUPPORT"
    elif any(item["status"] == "SCHEMA_MISSING" for item in missingness):
        status = "SCHEMA_REVIEW_REQUIRED"
    elif psi >= policy.psi_investigate:
        status = "INVESTIGATE_SHIFT"
    elif psi >= policy.psi_review or any(item["status"] == "REVIEW" for item in missingness):
        status = "REVIEW_SHIFT"
    else:
        status = "NO_POLICY_FLAG"
    return {
        "report_version": 1,
        "status": status,
        "score_semantics": "uncalibrated_ranking_score_not_validated_fraud_probability",
        "population": "two_historical_strictly_ordered_elapsed_time_windows",
        "reference_rows": int(len(reference)),
        "observed_rows": int(len(observed)),
        "temporal_bounds": times,
        "score_column": score_col,
        "score_psi": psi,
        "psi_smoothing_pseudocount_per_bin": 0.5,
        "score_bins": bins,
        "score_summary": {
            "reference_mean": float(ref_scores.mean()),
            "observed_mean": float(obs_scores.mean()),
            "reference_p95": float(np.quantile(ref_scores, 0.95)),
            "observed_p95": float(np.quantile(obs_scores, 0.95)),
        },
        "feature_missingness": missingness,
        "policy": {
            "psi_review": policy.psi_review,
            "psi_investigate": policy.psi_investigate,
            "missingness_change_review": policy.missingness_change_review,
            "min_reference_rows": policy.min_reference_rows,
            "min_observed_rows": policy.min_observed_rows,
        },
        "operator_action": (
            "Review time-window selection and source integrity, examine score/feature "
            "distribution changes and verify labeled outcome performance separately. "
            "Do not automatically retrain, promote models, decline transactions or "
            "claim a live production incident on the basis of these diagnostics."
        ),
        "labels_accessed": False,
        "real_time_evidence": False,
        "model_modified": False,
    }
