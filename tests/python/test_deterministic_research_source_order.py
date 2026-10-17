"""Deterministic research query-order tests — no real customer data."""
from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ml = importlib.import_module("src.prepare_raw_and_ml")


def test_stable_research_source_order_does_not_change_legacy_default() -> None:
    default = ml.feature_query("train", ["TransactionDT", "TransactionAmt"])
    stable = ml.feature_query("train", ["TransactionDT", "TransactionAmt"], stable_ties=True)
    assert 'order by t."TransactionDT"\n' in default
    assert 'order by t."TransactionDT", t."TransactionID"' in stable
    assert 'order by t."TransactionDT", t."TransactionID"' not in default


def test_identity_fingerprint_stable_with_same_timestamp_ties() -> None:
    with duckdb.connect(":memory:") as con:
        con.execute("CREATE SCHEMA raw")
        con.execute(
            "CREATE TABLE raw.train_transaction "
            "(TransactionID INTEGER, TransactionDT INTEGER, isFraud INTEGER, TransactionAmt DOUBLE)"
        )
        # Deliberately inserted in an order that is neither chronological
        # nor TransactionID-sorted for equal timestamps.
        con.execute(
            "INSERT INTO raw.train_transaction VALUES "
            "(308,20,0,5.0),(307,20,1,10.0),(315,10,0,9.0),(301,20,0,3.0)"
        )
        con.execute("CREATE TABLE raw.train_identity(TransactionID INTEGER)")
        sql = ml.feature_query("train", ["TransactionDT", "TransactionAmt"], stable_ties=True)
        fingerprints = []
        for _ in range(4):
            frame = con.execute(sql).fetch_df()
            assert frame["TransactionID"].tolist() == [315, 301, 307, 308]
            content = frame[["TransactionID", "TransactionDT", "isFraud"]].to_csv(index=False)
            fingerprints.append(hashlib.sha256(content.encode("utf-8")).hexdigest())
        assert len(set(fingerprints)) == 1
