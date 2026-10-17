"""Standard-library-only read access to private offline TreeSHAP artifacts.

The production HTTP module must not import numpy/SHAP/LightGBM. Reconstructing
attribution belongs exclusively to the authorized offline model pipeline.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def load_explanation(path: Path, transaction_id: int) -> dict[str, Any] | None:
    """Query only an existing SQLite artifact; never create an empty DB.

    Use parameterized SQL, no network access, and read-only URI mode.
    The API caller remains responsible for authentication and evidence gates.
    """
    resolved = Path(path).expanduser().resolve(strict=True)
    if not resolved.is_file() or resolved.suffix != ".sqlite":
        raise ValueError("Expected an existing private SQLite attribution store")
    with sqlite3.connect(resolved.as_uri() + "?mode=ro", uri=True, timeout=2) as connection:
        row = connection.execute(
            "SELECT payload_json FROM local_explanations WHERE transaction_id = ?",
            (int(transaction_id),),
        ).fetchone()
    if row is None:
        return None
    payload = json.loads(row[0])
    if not isinstance(payload, dict):
        raise ValueError("Malformed local explanation payload")
    return payload
