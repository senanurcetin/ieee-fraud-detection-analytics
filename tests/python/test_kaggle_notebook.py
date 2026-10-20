"""Notebook source and publication contracts, without Kaggle access or training."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_notebook_embeds_the_reviewed_comparison_implementation() -> None:
    notebook = json.loads((ROOT / "notebooks/ieee_cis_random_vs_time_reproduction.ipynb").read_text(encoding="utf-8"))
    script = (ROOT / "scripts/compare_random_time_holdout.py").read_text(encoding="utf-8")
    expected = ast.parse(script)
    expected.body = [
        node for node in expected.body
        if not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
        and not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                 and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__")
    ]
    code = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
    embedded = next(source for source in code if "def compare(" in source)
    assert ast.dump(ast.parse(embedded)) == ast.dump(expected)
    for index, source in enumerate(code):
        compile(source, f"notebook-cell-{index}", "exec")
    assert notebook["metadata"]["nexus"]["study_source_sha256"] == hashlib.sha256(script.encode()).hexdigest()


def test_publication_uses_competition_data_and_cpu_without_embedded_credentials() -> None:
    metadata = json.loads((ROOT / "notebooks/kernel-metadata.json").read_text(encoding="utf-8"))
    assert metadata["competition_sources"] == ["ieee-fraud-detection"]
    assert metadata["enable_gpu"] is False and metadata["enable_tpu"] is False
    assert metadata["enable_internet"] is False
    assert (ROOT / "notebooks" / metadata["code_file"]).is_file()
    assert not any(key in metadata for key in ("token", "api_key", "credentials"))


def test_recovered_original_source_is_retained_without_fabricated_outputs() -> None:
    path = ROOT / "notebooks/archive/original_ieee_cis_leakage.ipynb"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "53ad6dec337c1297db8dbcc6ef31f045945360ed3b8319544cc5b47df4a33457"
    log = ROOT / "docs/research/evidence/original_execution_log.txt"
    assert hashlib.sha256(log.read_bytes()).hexdigest() == "4f58ba866448bf9018a33fa86afd1e4c0f294c68fac02c494102ffffcdb79e70"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert all(not cell.get("outputs") for cell in notebook["cells"])


def test_completed_companion_evidence_is_full_source_and_strictly_temporal() -> None:
    report = json.loads((ROOT / "docs/research/evidence/ieee_cis_split_comparison.json").read_text())
    assert report["rows"] == 590540 and report["subset_mode"] is False
    assert report["input_sha256"] == "3a5c83ab6b3cc13dcabe5ffa9f522307fd5f7f7b6e6f6a60c32284ca6283d642"
    assert len(report["predictors"]) == 58
    assert {"TransactionDT", "TransactionID", "isFraud"}.isdisjoint(report["predictors"])
    for split in report["splits"].values():
        assert split["train_rows"] + split["holdout_rows"] == report["rows"]
        assert split["seen_proxy_subset"]["n"] + split["unseen_proxy_subset"]["n"] == split["holdout_rows"]
    temporal = report["splits"]["chronological"]
    assert temporal["train_max_transaction_dt"] < temporal["holdout_min_transaction_dt"]
