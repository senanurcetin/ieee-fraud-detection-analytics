"""Fit-window-only preprocessing and timestamp-safe splits for IEEE-CIS research.

This module is intentionally independent of the published model artifact and
does not change the historical dashboard scores or registry. Every learned
category vocabulary and Vesta missingness filter is fitted *only* on the rows
passed to fit(), not on temporal validation or Kaggle test observations.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def chronological_holdout(
    transaction_dt: pd.Series, train_fraction: float = 0.8
) -> tuple[np.ndarray, np.ndarray]:
    """Return positional fit/holdout indices with no shared timestamp boundary."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be strictly between zero and one")
    timestamps = pd.to_numeric(transaction_dt, errors="coerce").to_numpy(dtype="float64")
    if len(timestamps) < 4 or not np.isfinite(timestamps).all():
        raise ValueError("Require at least four finite TransactionDT values")

    # Stable sort preserves deterministic tie handling; ties are all in one side.
    order = np.argsort(timestamps, kind="stable")
    desired = max(1, min(int(np.floor(len(order) * train_fraction)), len(order) - 1))
    boundary = timestamps[order[desired]]
    fit = order[timestamps[order] < boundary]
    holdout = order[timestamps[order] >= boundary]
    if not len(fit) or not len(holdout):
        raise ValueError("No strict chronological boundary is possible")
    if timestamps[fit].max() >= timestamps[holdout].min():
        raise AssertionError("Chronological split boundaries overlap")
    return fit, holdout


def expanding_time_splits(
    transaction_dt: pd.Series,
    windows: int = 3,
    min_train_rows: int = 10_000,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding fit windows and disjoint subsequent validation windows.

    The caller must supply the *fit/development period only*. Never include
    final holdout rows here. Timestamp ties are kept on the same side.
    """
    if windows < 1 or min_train_rows < 1:
        raise ValueError("windows and min_train_rows must be positive")
    values = pd.to_numeric(transaction_dt, errors="coerce").to_numpy(dtype="float64")
    if len(values) < min_train_rows + windows or not np.isfinite(values).all():
        return []
    order = np.argsort(values, kind="stable")
    ordered_time = values[order]

    # Generate candidate cuts on row counts, then align to complete timestamp
    # groups to avoid accidental leakage at equality boundaries.
    cuts = [min_train_rows + ((len(order) - min_train_rows) * i) // windows
            for i in range(windows + 1)]
    boundaries = [min_train_rows]
    for cut in cuts[1:-1]:
        if cut >= len(order):
            continue
        boundaries.append(int(np.searchsorted(ordered_time, ordered_time[cut], side="left")))
    boundaries.append(len(order))
    start = int(np.searchsorted(ordered_time, ordered_time[min_train_rows], side="left"))
    boundaries[0] = start
    result: list[tuple[np.ndarray, np.ndarray]] = []
    for a, b in zip(boundaries[:-1], boundaries[1:], strict=True):
        if a < min_train_rows or b <= a or a >= len(order):
            continue
        fit = order[:a]
        valid = order[a:b]
        if ordered_time[a - 1] >= ordered_time[a]:
            continue
        if len(valid) and values[fit].max() < values[valid].min():
            result.append((fit, valid))
    return result


@dataclass
class FoldPreprocessor:
    """Learn category codes and V selection strictly from the fit period.

    Unknown categories and null values map to -1; for LightGBM's native
    categorical mode negative codes represent missing, not a learned category.
    """

    categorical_columns: tuple[str, ...]
    v_missingness_threshold: float = 0.95

    def fit(self, frame: pd.DataFrame) -> FoldPreprocessor:
        if frame.empty:
            raise ValueError("Fit frame must be nonempty")
        if not 0 <= self.v_missingness_threshold <= 1:
            raise ValueError("v_missingness_threshold must be between 0 and 1")
        self.feature_names_: list[str] = []
        self.categorical_: list[str] = []
        self.category_maps_: dict[str, dict[str, int]] = {}
        self.v_missingness_: dict[str, float] = {}
        names = set(self.categorical_columns)
        for col in frame.columns:
            is_v = col.startswith("V") and col[1:].isdigit()
            if is_v:
                missing = float(frame[col].isna().mean())
                self.v_missingness_[col] = missing
                if missing > self.v_missingness_threshold:
                    continue
            self.feature_names_.append(col)
            if col in names:
                tokens = frame[col].astype("string").dropna().unique().tolist()
                # Stable, order-independent vocabulary from fit rows only.
                ordered = sorted(str(token) for token in tokens)
                self.category_maps_[col] = {value: i for i, value in enumerate(ordered)}
                self.categorical_.append(col)
        if not self.feature_names_:
            raise ValueError("No features survive fit-only selection")
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not hasattr(self, "feature_names_"):
            raise ValueError("Fit the preprocessor before calling transform")
        missing_columns = sorted(set(self.feature_names_) - set(frame.columns))
        if missing_columns:
            raise ValueError(f"Missing required feature columns: {missing_columns}")
        result = pd.DataFrame(index=frame.index)
        for col in self.feature_names_:
            if col in self.category_maps_:
                result[col] = (
                    frame[col]
                    .astype("string")
                    .map(self.category_maps_[col])
                    .fillna(-1)
                    .astype("int32")
                )
            else:
                result[col] = pd.to_numeric(frame[col], errors="coerce").astype("float32")
        return result

    def fit_transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        return self.fit(frame).transform(frame)


def training_risk_band_edges(fit_scores: np.ndarray) -> dict[str, float]:
    """Learn risk score cutoffs using only development *fit* predictions."""
    scores = np.asarray(fit_scores, dtype="float64")
    if scores.ndim != 1 or scores.size == 0 or not np.isfinite(scores).all():
        raise ValueError("Fit scores must be a nonempty finite 1D vector")
    if np.any((scores < 0) | (scores > 1)):
        raise ValueError("Fit scores must lie between zero and one")
    q80, q95, q99 = np.quantile(scores, [0.80, 0.95, 0.99])
    return {"elevated_p80": float(q80), "high_p95": float(q95), "critical_p99": float(q99)}
