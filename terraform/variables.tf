variable "project_id" {
  description = "GCP Project ID — find this in the GCP console top bar"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "europe-west3"
  # europe-west3 is Frankfurt — closest to Koblenz, lowest latency
}

variable "environment" {
  description = "Deployment environment label"
  type        = string
  default     = "prod"
  # Used to tag resources so you know what they belong to
}

variable "gcs_bucket_raw" {
  description = "GCS bucket for raw ingested data — must be globally unique"
  type        = string
  # Format: citybikes-raw-YOUR_PROJECT_ID
}

variable "gcs_bucket_processed" {
  description = "GCS bucket for processed/validated data — must be globally unique"
  type        = string
}

variable "gcs_bucket_snapshots" {
  description = "GCS bucket for monthly mart exports — must be globally unique"
  type        = string
}

variable "bq_dataset_raw" {
  description = "BigQuery dataset for external tables pointing at GCS"
  type        = string
  default     = "citybikes_raw"
}

variable "bq_dataset_staging" {
  description = "BigQuery dataset for dbt staging models"
  type        = string
  default     = "citybikes_staging"
}

variable "bq_dataset_mart" {
  description = "BigQuery dataset for dbt mart models (facts and dimensions)"
  type        = string
  default     = "citybikes_mart"
}
