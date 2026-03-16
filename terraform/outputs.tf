output "gcs_bucket_raw" {
  description = "Name of the raw GCS bucket"
  value       = google_storage_bucket.raw.name
}

output "gcs_bucket_processed" {
  description = "Name of the processed GCS bucket"
  value       = google_storage_bucket.processed.name
}

output "gcs_bucket_snapshots" {
  description = "Name of the snapshots GCS bucket"
  value       = google_storage_bucket.snapshots.name
}


output "bq_dataset_raw" {
  description = "BigQuery raw dataset ID"
  value       = google_bigquery_dataset.raw.dataset_id
}

output "bq_dataset_staging" {
  description = "BigQuery staging dataset ID"
  value       = google_bigquery_dataset.staging.dataset_id
}

output "bq_dataset_mart" {
  description = "BigQuery mart dataset ID"
  value       = google_bigquery_dataset.mart.dataset_id
}

output "artifact_registry_url" {
  description = "Docker image registry URL — use this when pushing images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/citybikes-de"
}

output "service_account_ingestion" {
  description = "Ingestion service account email"
  value       = google_service_account.ingestion.email
}

output "service_account_dbt" {
  description = "dbt service account email"
  value       = google_service_account.dbt.email
}

output "service_account_kestra" {
  description = "Kestra service account email"
  value       = google_service_account.kestra.email
}
