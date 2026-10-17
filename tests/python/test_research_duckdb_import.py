"""Offline contracts for the manual, secret-safe Kaggle research execution."""
from __future__ import annotations

import csv
import importlib
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
prepare = importlib.import_module("scripts.prepare_research_duckdb").prepare


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def source(tmp_path: Path, *, duplicate: bool = False) -> Path:
    folder = tmp_path / "input"
    folder.mkdir()
    write_csv(
        folder / "train_transaction.csv",
        ["TransactionID", "TransactionDT", "isFraud", "TransactionAmt", "ProductCD", "V1"],
        [[11, 100, 0, 10, "W", 0.4], [12, 200, 1, 20, "C", 0.9],
         [11 if duplicate else 13, 300, 0, 30, "W", 0.7]],
    )
    write_csv(
        folder / "train_identity.csv",
        ["TransactionID", "DeviceType", "id_01"],
        [[11, "mobile", 1.0], [12, "desktop", 2.0]],
    )
    return folder


def test_research_import_builds_only_original_train_tables(tmp_path: Path) -> None:
    origin = source(tmp_path)
    database = tmp_path / "output" / "experiment.duckdb"
    counts = prepare(origin, database, expected={"train_transaction": 3, "train_identity": 2})
    assert counts == {"train_transaction": 3, "train_identity": 2}
    with duckdb.connect(str(database), read_only=True) as con:
        actual = {
            row[0] for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='raw'"
            ).fetchall()
        }
        assert actual == {"train_transaction", "train_identity"}
        assert con.execute("SELECT SUM(isFraud) FROM raw.train_transaction").fetchone()[0] == 1


def test_research_import_refuses_partial_or_wrong_source(tmp_path: Path) -> None:
    origin = source(tmp_path)
    (origin / "train_identity.csv").unlink()
    with pytest.raises(FileNotFoundError):
        prepare(origin, tmp_path / "bad.duckdb", expected={"train_transaction": 3, "train_identity": 2})

    source2 = tmp_path / "different"
    origin.rename(source2)
    write_csv(source2 / "train_identity.csv", ["TransactionID"], [[11], [12]])
    with pytest.raises(ValueError, match="unexpected row count"):
        prepare(source2, tmp_path / "other.duckdb")


def test_research_import_rejects_duplicate_transaction_ids(tmp_path: Path) -> None:
    origin = source(tmp_path, duplicate=True)
    with pytest.raises(ValueError, match="Duplicate"):
        prepare(
            origin, tmp_path / "dup.duckdb",
            expected={"train_transaction": 3, "train_identity": 2},
        )


def test_github_research_workflow_never_runs_on_push_or_exports_raw_files() -> None:
    path = ROOT / ".github/workflows/kaggle-research-evidence.yml"
    workflow = path.read_text(encoding="utf-8")
    assert "\n  workflow_dispatch:" in workflow
    assert "\n  push:" not in workflow
    assert "\n  pull_request:" not in workflow
    assert "contents: read" in workflow
    assert "KAGGLE_API_TOKEN: ${{ secrets.KAGGLE_API_TOKEN }}" in workflow
    assert "outputs/research/research_report.json" in workflow
    assert "outputs/research/source_manifest.json" in workflow
    assert "data/raw/kaggle_ieee_fraud\n" not in workflow.split("uses: actions/upload-artifact@v4")[1].split("if-no-files-found:")[0]
    assert "timeout-minutes: 35" in workflow
    assert "if: always()" in workflow
