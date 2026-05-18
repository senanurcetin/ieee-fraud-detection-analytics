from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = ROOT / "outputs" / "powerbi"


def main() -> None:
    PBI_DIR.mkdir(parents=True, exist_ok=True)
    folder_pbids = {
        "version": "0.1",
        "connections": [
            {
                "details": {
                    "protocol": "folder",
                    "address": {
                        "path": str(PBI_DIR.resolve()),
                    },
                },
                "mode": "Import",
            }
        ],
    }
    (PBI_DIR / "ieee_fraud_csv_folder.pbids").write_text(
        json.dumps(folder_pbids, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    bigquery_m = """// Power BI > Get Data > Google BigQuery > Advanced options > SQL statement
// Project: workintech-working
// Dataset: powerbi

SELECT * FROM `workintech-working.powerbi.fact_train_transactions`;
SELECT * FROM `workintech-working.powerbi.mart_model_predictions`;
SELECT * FROM `workintech-working.powerbi.mart_fraud_summary`;
SELECT * FROM `workintech-working.powerbi.mart_daily_stats`;
SELECT * FROM `workintech-working.powerbi.mart_amount_bands`;
SELECT * FROM `workintech-working.powerbi.mart_product_device_stats`;
SELECT * FROM `workintech-working.powerbi.mart_email_domain_stats`;
SELECT * FROM `workintech-working.powerbi.mart_risk_band_stats`;
SELECT * FROM `workintech-working.powerbi.mart_feature_missingness`;
"""
    (PBI_DIR / "bigquery_powerbi_sql.txt").write_text(bigquery_m, encoding="utf-8")


if __name__ == "__main__":
    main()
