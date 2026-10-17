"""Prepare a restricted local DuckDB source for read-only IEEE-CIS research.

This avoids the full 500-estimator production pipeline when experiments only
need train_transaction/train_identity. No remote data, uploads or model promotion.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

REQUIRED = ("train_transaction", "train_identity")
EXPECTED_ROWS = {"train_transaction": 590_540, "train_identity": 144_233}


def prepare(source: Path, destination: Path, *, expected: dict[str, int] | None = None) -> dict[str, int]:
    """Import the two original Kaggle train CSVs and enforce exact source counts."""
    expected = EXPECTED_ROWS if expected is None else expected
    paths = {name: (source / f"{name}.csv") for name in REQUIRED}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(f"Required competition source unavailable: {path.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    with duckdb.connect(str(destination)) as con:
        con.execute("SET threads=2")
        con.execute("SET memory_limit='3GB'")
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        for name, path in paths.items():
            con.execute(
                f"CREATE OR REPLACE TABLE raw.{name} AS "
                "SELECT * FROM read_csv_auto(?, header=true, sample_size=200000, "
                "nullstr=['', 'NA', 'null'])",
                [str(path.resolve())],
            )
            counts[name] = con.execute(f"SELECT COUNT(*) FROM raw.{name}").fetchone()[0]
            if counts[name] != expected[name]:
                raise ValueError(f"{name}: unexpected row count (expected {expected[name]}, actual {counts[name]})")
        columns = {
            name: {row[1] for row in con.execute(f"PRAGMA table_info('raw.{name}')").fetchall()}
            for name in REQUIRED
        }
        if not {"TransactionID", "TransactionDT", "isFraud"}.issubset(columns["train_transaction"]):
            raise ValueError("train_transaction required columns are missing")
        if "TransactionID" not in columns["train_identity"]:
            raise ValueError("train_identity required key is missing")
        distinct = con.execute("SELECT COUNT(DISTINCT TransactionID) FROM raw.train_transaction").fetchone()[0]
        if distinct != counts["train_transaction"]:
            raise ValueError("Duplicate train TransactionID values")
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/raw/kaggle_ieee_fraud"))
    parser.add_argument("--duckdb", type=Path, default=Path("data/processed/ieee_fraud.duckdb"))
    args = parser.parse_args(argv)
    counts = prepare(args.source, args.duckdb)
    print(f"PASS: original competition train row counts validated: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
