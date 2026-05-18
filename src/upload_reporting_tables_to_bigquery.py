from __future__ import annotations

import argparse
import os
from pathlib import Path

from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = ROOT / "outputs" / "powerbi"

DEFAULT_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "workintech-working")
DEFAULT_LOCATION = os.environ.get("BIGQUERY_LOCATION", "US")
DEFAULT_DATASET = os.environ.get("BIGQUERY_REPORTING_DATASET", "fraud_project_powerbi")

REPORTING_FILES = [
    "mart_fraud_summary.csv",
    "mart_daily_stats.csv",
    "mart_amount_bands.csv",
    "mart_product_device_stats.csv",
    "mart_email_domain_stats.csv",
    "mart_feature_missingness.csv",
    "mart_model_predictions.csv",
    "mart_risk_band_stats.csv",
    "fact_train_transactions.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload Power BI reporting CSV marts to BigQuery.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--credentials", default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    return parser.parse_args()


def create_dataset(client: bigquery.Client, project_id: str, dataset_id: str, location: str) -> None:
    dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
    dataset.location = location
    client.create_dataset(dataset, exists_ok=True)


def load_csv(client: bigquery.Client, project_id: str, dataset: str, path: Path) -> None:
    table_name = path.stem
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        null_marker="",
    )
    with path.open("rb") as handle:
        job = client.load_table_from_file(handle, f"{project_id}.{dataset}.{table_name}", job_config=job_config)
    job.result()
    table = client.get_table(f"{project_id}.{dataset}.{table_name}")
    print(f"Loaded {project_id}.{dataset}.{table_name}: {table.num_rows:,} rows")


def main() -> None:
    args = parse_args()
    if not args.credentials:
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS is not set. Pass --credentials or set the environment variable.")
    credential_path = Path(args.credentials)
    if not credential_path.exists():
        raise FileNotFoundError(f"Credential file not found: {credential_path}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credential_path)
    client = bigquery.Client(project=args.project_id, location=args.location)
    create_dataset(client, args.project_id, args.dataset, args.location)

    for file_name in REPORTING_FILES:
        path = PBI_DIR / file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing reporting file: {path}")
        load_csv(client, args.project_id, args.dataset, path)

    print(f"Reporting dataset ready: {args.project_id}.{args.dataset}")


if __name__ == "__main__":
    main()
