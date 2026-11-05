"""Tests for scripts/benchmark_rapids_gpu.py that need neither a GPU nor the Kaggle download."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("benchmark_rapids_gpu", ROOT / "scripts" / "benchmark_rapids_gpu.py")
bench = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bench
spec.loader.exec_module(bench)

RESULTS = ROOT / "docs" / "data" / "rapids-benchmark"


def test_sparse_v_columns_follow_the_pipeline_threshold():
    df = pd.DataFrame({"V1": [1.0] * 100, "V2": [np.nan] * 96 + [1.0] * 4, "V3": [np.nan] * 95 + [1.0] * 5})
    kept, n_v = bench.drop_sparse_v(df)
    # V2 is 96% missing (> 0.95) and is dropped; V3 is exactly 95% missing and is kept, as in the pipeline.
    assert list(kept.columns) == ["V1", "V3"]
    assert n_v == 2


def test_categoricals_become_int32_codes_with_minus_one_for_missing():
    df = pd.DataFrame({"ProductCD": ["W", None, "C", "W"], "card4": ["visa", "visa", None, "amex"]})
    out = bench.encode_categoricals(df)
    assert out["ProductCD"].dtype == "int32"
    assert out["ProductCD"].tolist()[1] == -1
    assert out.loc[0, "ProductCD"] == out.loc[3, "ProductCD"]


def test_aggregates_match_a_plain_groupby():
    df = pd.DataFrame(
        {
            "card1": [1, 1, 2, 2, 2],
            "addr1": [10, 20, 10, 10, 20],
            "P_emaildomain": [0, 0, 1, 1, 1],
            "TransactionAmt": np.array([10, 20, 5, 5, 20], dtype="float32"),
        }
    )
    out = bench.add_aggregates(df.copy())
    expected = df.groupby("card1")["TransactionAmt"].transform("mean")
    np.testing.assert_allclose(out["TransactionAmt_mean_by_card1"], expected)
    assert out["TransactionAmt_count_by_addr1"].tolist() == [3, 2, 3, 3, 2]
    assert len(out) == len(df)


def _range(a: float, b: float) -> str:
    lo, hi = sorted((round(a, 3), round(b, 3)))
    return f"{lo:g} – {hi:g}"


def test_readme_table_quotes_the_recorded_results():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## GPU acceleration with RAPIDS", 1)[1].split("\n## ", 1)[0]
    for name in ("gpu.json", "cpu_windows.json"):
        report = json.loads((RESULTS / name).read_text())
        cold, warm = report["cold_run"], report["warm_run"]
        assert cold["rows"] == warm["rows"] == 590540
        read = (cold["steps_s"]["read_csv"], warm["steps_s"]["read_csv"])
        rest = (cold["pipeline_total_s"] - read[0], warm["pipeline_total_s"] - read[1])
        for a, b in (read, rest, (cold["steps_s"]["xgboost_fit"], warm["steps_s"]["xgboost_fit"]),
                     (cold["total_s"], warm["total_s"])):
            assert _range(a, b) in section, (name, a, b)
        assert f"{warm['valid_roc_auc']} / {warm['valid_average_precision']}" in section
