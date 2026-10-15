"""Notebook syntax, provenance and no-fake-output contracts."""
import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ResearchNotebookContractTests(unittest.TestCase):
    def test_notebook_is_parseable_unexecuted_and_data_gated(self):
        names = [
            ROOT / "research" / "ieee_cis_split_audit_reconstruction.ipynb",
            ROOT / "research" / "neu_cls_robustness_reconstruction.ipynb",
        ]
        existing = [path for path in names if path.exists()]
        self.assertEqual(len(existing), 1, "Expected exactly this repository's research reconstruction")
        notebook = json.loads(existing[0].read_text(encoding="utf-8"))
        self.assertEqual(notebook["nbformat"], 4)
        source = ""
        for cell in notebook["cells"]:
            value = "".join(cell["source"])
            if cell["cell_type"] == "code":
                ast.parse(value)
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])
                source += value
        self.assertIn("raise FileNotFoundError", source)
        self.assertIn("NOT EXECUTED", "".join(notebook["cells"][0]["source"]))
