from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = ROOT / "outputs" / "powerbi"
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "your-gcp-project")
REPORTING_DATASET = "fraud_project_powerbi"


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
    (PBI_DIR / "fraud_project_csv_folder.pbids").write_text(
        json.dumps(folder_pbids, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    bigquery_m = f"""// Power BI > Get Data > Google BigQuery > Advanced options > SQL statement
// Project: {PROJECT_ID}
// Dataset: {REPORTING_DATASET}

SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.fact_train_transactions`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_executive_kpis`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_product_risk`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_identity_risk`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_amount_bands`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_email_domain_risk`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_model_risk_bands`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_segment_watchlist`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_review_strategy`;
SELECT * FROM `{PROJECT_ID}.{REPORTING_DATASET}.pbi_data_quality_scorecard`;
"""
    (PBI_DIR / "bigquery_powerbi_sql.txt").write_text(bigquery_m, encoding="utf-8")


if __name__ == "__main__":
    main()
