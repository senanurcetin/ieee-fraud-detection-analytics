"""Verifiable instance-level LightGBM TreeSHAP, stored as an offline SQLite artifact.

Only model-derived local attributions with validated raw-margin additivity may
receive the label TreeSHAP. No transaction values, labels, or client identities
are embedded in the per-case payload. Feature names are masked in IEEE-CIS.
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import tempfile
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path
from typing import Any

import numpy as np

EXPLANATION_VERSION = 1
MAX_LOCAL_FACTORS = 12


def _positive_class_contributions(values: Any, feature_count: int) -> np.ndarray:
    """Handle SHAP 0.x binary output as matrix, class list, or 3-D array."""
    if isinstance(values, list):
        if not values or len(values) > 2:
            raise ValueError("Unsupported SHAP binary class structure")
        values = values[-1]
    a = np.asarray(values, dtype="float64")
    if a.ndim == 3 and a.shape[2] == 2:
        a = a[:, :, 1]
    if a.ndim != 2 or a.shape[1] != feature_count or not np.isfinite(a).all():
        raise ValueError("Expected finite SHAP matrix with exactly one value per feature")
    return a


def _positive_class_expected_value(value: Any) -> float:
    a = np.asarray(value, dtype="float64")
    if a.ndim == 0:
        expected = float(a)
    elif a.ndim == 1 and a.size in (1, 2):
        expected = float(a[-1])
    else:
        raise ValueError("Unexpected TreeSHAP binary expected value")
    if not math.isfinite(expected):
        raise ValueError("Nonfinite TreeSHAP expected raw margin")
    return expected


def build_local_shap_explanations(
    *,
    transaction_ids: Sequence[int],
    feature_names: Sequence[str],
    shap_values: Any,
    expected_value: Any,
    raw_margins: Sequence[float],
    ranking_scores: Sequence[float],
    model_version: str,
    sample_scope: str = "validation_holdout_sample",
    top_k: int = 8,
    additivity_atol: float = 1e-3,
) -> list[dict[str, Any]]:
    """Refuse a local explanation unless full-feature raw-margin SHAP adds up."""
    features = list(feature_names)
    if not features or len(features) != len(set(features)):
        raise ValueError("Features must be nonempty, uniquely named and ordered")
    if not model_version.strip() or sample_scope != "validation_holdout_sample":
        raise ValueError("Model version and validated source scope required")
    if not 1 <= top_k <= MAX_LOCAL_FACTORS or additivity_atol <= 0:
        raise ValueError("Invalid local explanation limits")
    impacts = _positive_class_contributions(shap_values, len(features))
    n = impacts.shape[0]
    ids = [int(x) for x in transaction_ids]
    raw = np.asarray(raw_margins, dtype="float64")
    score = np.asarray(ranking_scores, dtype="float64")
    if len(ids) != n or len(set(ids)) != n or raw.shape != (n,) or score.shape != (n,):
        raise ValueError("Transaction IDs, raw margins and scores must align uniquely")
    if not np.isfinite(raw).all() or not np.isfinite(score).all() or np.any((score < 0) | (score > 1)):
        raise ValueError("Model scores must be finite, with ranking scores in [0,1]")
    if n == 0:
        raise ValueError("At least one measured transaction is required")

    base = _positive_class_expected_value(expected_value)
    summed = impacts.sum(axis=1)
    residual = base + summed - raw
    if np.max(np.abs(residual)) > additivity_atol:
        raise ValueError("Local TreeSHAP does not reconstruct LightGBM raw margins")
    # The scalar predict_proba is a *ranking score*, not a calibrated empirical probability.
    reconstructed_scores = 1 / (1 + np.exp(-np.clip(raw, -700, 700)))
    if not np.allclose(reconstructed_scores, score, atol=1e-4, rtol=1e-4):
        raise ValueError("Published scoring vector does not correspond to model raw margins")

    output: list[dict[str, Any]] = []
    for row, transaction_id in enumerate(ids):
        order = np.argsort(-np.abs(impacts[row]), kind="stable")[:top_k]
        factors = [
            {
                "feature": features[int(idx)],
                "shap_raw_margin": float(impacts[row, idx]),
                "direction": "raises_model_score" if impacts[row, idx] > 0 else (
                    "lowers_model_score" if impacts[row, idx] < 0 else "neutral"
                ),
            }
            for idx in order
        ]
        top_sum = float(sum(factor["shap_raw_margin"] for factor in factors))
        output.append({
            "transaction_id": transaction_id,
            "method": "TreeSHAP",
            "output_space": "LightGBM raw margin (log odds)",
            "calibrated_probability": False,
            "label_source": "no_labels_in_explanation_artifact",
            "model_version": model_version,
            "sample_scope": sample_scope,
            "explanation_version": EXPLANATION_VERSION,
            "feature_count": len(features),
            "reported_factor_count": len(factors),
            "base_raw_margin": base,
            "sum_all_feature_contributions": float(summed[row]),
            "top_factor_sum": top_sum,
            "omitted_factor_sum": float(summed[row] - top_sum),
            "raw_model_margin": float(raw[row]),
            "raw_margin_additivity_residual": float(residual[row]),
            "uncalibrated_ranking_score": float(score[row]),
            "factors": factors,
            "methodology": (
                "Local feature attributions are model-specific associations, not causal evidence. "
                "Anonymous Vesta fields lack verified real-world semantics. "
                "The displayed ranking score is not a calibrated fraud probability."
            ),
        })
    return output


def save_explanations(path: Path, explanations: Sequence[dict[str, Any]]) -> None:
    """Atomically replace a private read-only-queryable artifact; never publish by default."""
    destination = Path(path)
    if not explanations:
        raise ValueError("Cannot save an empty SHAP cohort")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=".local-shap-", suffix=".sqlite", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(fd, "rb"):
            pass
        with closing(sqlite3.connect(temporary)) as conn, conn:
            conn.execute(
                "create table local_explanations ("
                "transaction_id integer primary key, model_version text not null, payload_json text not null)"
            )
            for payload in explanations:
                if payload.get("method") != "TreeSHAP" or abs(
                    float(payload.get("raw_margin_additivity_residual", math.inf))
                ) > 1e-3:
                    raise ValueError("Artifact includes an invalid or unverified explanation")
                conn.execute(
                    "insert into local_explanations values (?, ?, ?)",
                    (
                        int(payload["transaction_id"]),
                        str(payload["model_version"]),
                        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                    ),
                )
            conn.execute("create table artifact_metadata (key text primary key, value text not null)")
            conn.execute(
                "insert into artifact_metadata values (?, ?)",
                ("explanation_schema", str(EXPLANATION_VERSION)),
            )
            conn.commit()
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def load_explanation(path: Path, transaction_id: int) -> dict[str, Any] | None:
    """Lookup without SQL writes; callers must enforce API authorization."""
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        row = conn.execute(
            "select payload_json from local_explanations where transaction_id=?",
            (int(transaction_id),),
        ).fetchone()
    return json.loads(row[0]) if row is not None else None
