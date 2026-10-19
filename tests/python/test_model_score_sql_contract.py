"""Execute the dbt model-score contract against offline DuckDB fixtures."""
from pathlib import Path

import duckdb


def test_model_score_contract_rejects_missing_and_invalid_risk_bands() -> None:
    contract = (Path(__file__).resolve().parents[1] / "assert_model_score_contract.sql").read_text(
        encoding="utf-8"
    )
    query = contract.replace("{{ ref('mart_model_predictions') }}", "predictions")
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE predictions (transaction_id INTEGER, split VARCHAR, "
            "actual_is_fraud INTEGER, predicted_fraud_probability DOUBLE, risk_band VARCHAR)"
        )
        con.executemany(
            "INSERT INTO predictions VALUES (?, ?, ?, ?, ?)",
            [
                (1, "train", 0, 0.1, "Low"),
                (2, "train", 1, 0.4, "Elevated"),
                (3, "test", None, 0.8, "High"),
                (4, "test", None, 1.0, "Critical"),
                (5, "train", 1, 0.8, None),
                (6, "train", 0, 0.1, "Unknown"),
                (7, "test", None, 0.2, ""),
            ],
        )
        rejected = con.execute(query).fetchall()
    assert {row[0] for row in rejected} == {5, 6, 7}
