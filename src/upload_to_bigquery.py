from __future__ import annotations

import os
import argparse
from pathlib import Path

import duckdb
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "kaggle_ieee_fraud"
DB_PATH = ROOT / "data" / "processed" / "ieee_fraud.duckdb"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "workintech-working")
LOCATION = os.environ.get("BIGQUERY_LOCATION", "US")


RAW_FILES = {
    "train_transaction": RAW_DIR / "train_transaction.csv",
    "train_identity": RAW_DIR / "train_identity.csv",
    "test_transaction": RAW_DIR / "test_transaction.csv",
    "test_identity": RAW_DIR / "test_identity.csv",
    "sample_submission": RAW_DIR / "sample_submission.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload raw IEEE-CIS files and model support tables to BigQuery.")
    parser.add_argument("--project-id", default=PROJECT_ID)
    parser.add_argument("--location", default=LOCATION)
    parser.add_argument("--credentials", default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    return parser.parse_args()


def create_dataset(client: bigquery.Client, dataset_id: str) -> None:
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{dataset_id}")
    dataset.location = LOCATION
    client.create_dataset(dataset, exists_ok=True)


def load_csv(client: bigquery.Client, dataset: str, table: str, path: Path) -> None:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        null_marker="",
    )
    with path.open("rb") as fh:
        job = client.load_table_from_file(fh, f"{PROJECT_ID}.{dataset}.{table}", job_config=job_config)
    job.result()
    destination = client.get_table(f"{PROJECT_ID}.{dataset}.{table}")
    print(f"Loaded {destination.full_table_id}: {destination.num_rows:,} rows")


def load_duckdb_table(client: bigquery.Client, dataset: str, table: str, duckdb_table: str) -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(f"select * from {duckdb_table}").fetch_df()
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, autodetect=True)
    job = client.load_table_from_dataframe(df, f"{PROJECT_ID}.{dataset}.{table}", job_config=job_config)
    job.result()
    destination = client.get_table(f"{PROJECT_ID}.{dataset}.{table}")
    print(f"Loaded {destination.full_table_id}: {destination.num_rows:,} rows")


def main() -> None:
    args = parse_args()
    global PROJECT_ID, LOCATION
    PROJECT_ID = args.project_id
    LOCATION = args.location
    if not args.credentials:
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS is not set. Pass --credentials or set the environment variable.")
    credential_path = Path(args.credentials)
    if not credential_path.exists():
        raise FileNotFoundError(f"Credential file not found: {credential_path}")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credential_path)

    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    for dataset in ["raw", "staging", "intermediate", "mart", "dbt_default"]:
        create_dataset(client, dataset)
    for table, path in RAW_FILES.items():
        load_csv(client, "raw", table, path)
    load_duckdb_table(client, "raw", "feature_missingness", "raw.feature_missingness")
    load_duckdb_table(client, "raw", "ml_predictions", "raw.ml_predictions")
    print("Next: dbt run --project-dir dbt_ieee_fraud --profiles-dir profiles --profile ieee_fraud_detection --target prod")


if __name__ == "__main__":
    main()
