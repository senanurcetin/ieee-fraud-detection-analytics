output "dataset_ids" {
  description = "Created BigQuery dataset ids."
  value       = [for dataset in google_bigquery_dataset.fraud_project : dataset.dataset_id]
}
