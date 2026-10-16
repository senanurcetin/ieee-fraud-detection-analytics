"""Data-free regression tests for genuine random/time leakage comparison."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "compare_random_time_holdout.py"
spec = importlib.util.spec_from_file_location("compare_random_time_holdout", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture() -> pd.DataFrame:
    n = 240
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "isFraud": np.tile([0, 0, 0, 1], n // 4),
        "TransactionDT": np.arange(n),
        "TransactionAmt": rng.uniform(4, 90, n),
        "card1": np.arange(n) % 15,
        "card2": np.arange(n) % 9,
        "card3": 1,
        "card5": 2,
        "addr1": np.arange(n) % 11,
    })


def test_split_no_time_overlap_and_full_partition():
    df = fixture()
    splits = module.split_indices(df)
    for fit, holdout in splits.values():
        assert len(fit) + len(holdout) == len(df)
        assert len(set(fit) & set(holdout)) == 0
    fit, holdout = splits["chronological"]
    assert df.TransactionDT.iloc[fit].max() < df.TransactionDT.iloc[holdout].min()


def test_comparison_is_data_derived_and_group_proxy_labeled():
    result = module.compare(fixture())
    assert set(result["splits"]) == {"random", "chronological"}
    assert result["rows"] == 240
    assert result["splits"]["chronological"]["holdout"]["n"] > 0
    assert "causal estimate" in result["interpretation_limit"]


def test_rejects_missing_classes_or_times():
    df = fixture()
    df["isFraud"] = 0
    with pytest.raises(ValueError):
        module.split_indices(df)
