# ============================================================
# GCS BUCKETS — the data lake
# ============================================================

# Raw bucket: stores Parquet files exactly as ingested
# Nothing is ever deleted or modified here — it's the source of truth
resource "google_storage_bucket" "raw" {
  name          = var.gcs_bucket_raw
  location      = var.region
  force_destroy = false  # Prevents accidental deletion with data inside

  # Organise storage by date automatically
  uniform_bucket_level_access = true

  versioning {
    enabled = false  # Not needed — Parquet files are immutable
  }

  labels = {
    environment = var.environment
    project     = "citybikes-de"
    layer       = "raw"
  }
}

# Processed bucket: stores validated, cleaned Parquet
resource "google_storage_bucket" "processed" {
  name          = var.gcs_bucket_processed
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    project     = "citybikes-de"
    layer       = "processed"
  }
}

# Snapshots bucket: monthly exports of mart tables
# These are the post-GCP-expiry fallback — downloaded and committed to repo
resource "google_storage_bucket" "snapshots" {
  name          = var.gcs_bucket_snapshots
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  # Auto-delete snapshot files after 365 days to control costs
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = "citybikes-de"
    layer       = "snapshots"
  }
}


# ============================================================
# BIGQUERY DATASETS
# ============================================================

# Raw dataset: contains external tables pointing at GCS
# No data is stored here — BQ reads directly from GCS Parquet files
resource "google_bigquery_dataset" "raw" {
  dataset_id  = var.bq_dataset_raw
  location    = var.region
  description = "External tables pointing at GCS raw zone. No data stored in BQ."

  labels = {
    environment = var.environment
    project     = "citybikes-de"
    layer       = "raw"
  }
}

# Staging dataset: dbt staging models land here
resource "google_bigquery_dataset" "staging" {
  dataset_id  = var.bq_dataset_staging
  location    = var.region
  description = "dbt staging models — cleaned and typed raw data."

  labels = {
    environment = var.environment
    project     = "citybikes-de"
    layer       = "staging"
  }
}

# Mart dataset: final fact and dimension tables used by dashboards
resource "google_bigquery_dataset" "mart" {
  dataset_id  = var.bq_dataset_mart
  location    = var.region
  description = "dbt mart models — fact tables and dimensions for analytics."

  labels = {
    environment = var.environment
    project     = "citybikes-de"
    layer       = "mart"
  }
}

# ============================================================
# ARTIFACT REGISTRY — Docker image storage
# ============================================================

# This is where we push the ingestion container image
# Cloud Run pulls the image from here when it runs the job
resource "google_artifact_registry_repository" "citybikes" {
  location      = var.region
  repository_id = "citybikes-de"
  description   = "Docker images for CityBikes DE pipeline"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    project     = "citybikes-de"
  }
}

# ============================================================
# SERVICE ACCOUNTS — identities for each component
# ============================================================

# Each service gets its own identity with only the permissions it needs
# This is "least privilege" — a security best practice

# Ingestion service account: used by the Cloud Run ingestion job
resource "google_service_account" "ingestion" {
  account_id   = "citybikes-ingestion"
  display_name = "CityBikes Ingestion Job"
  description  = "Used by the Cloud Run ingestion job to write to GCS and read secrets"
}

# dbt service account: used by dbt (locally and in CI) to query/write BigQuery
resource "google_service_account" "dbt" {
  account_id   = "citybikes-dbt"
  display_name = "CityBikes dbt Transformer"
  description  = "Used by dbt Core to read from BQ raw and write to BQ staging and mart"
}

# Kestra service account: used by Kestra to trigger Cloud Run jobs
resource "google_service_account" "kestra" {
  account_id   = "citybikes-kestra"
  display_name = "CityBikes Kestra Orchestrator"
  description  = "Used by Kestra to trigger Cloud Run jobs and read GCS"
}

# ============================================================
# IAM BINDINGS — grant permissions to service accounts
# ============================================================

# Ingestion SA: write to raw and processed GCS buckets
resource "google_storage_bucket_iam_member" "ingestion_raw_write" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.ingestion.email}"
}

resource "google_storage_bucket_iam_member" "ingestion_processed_write" {
  bucket = google_storage_bucket.processed.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.ingestion.email}"
}

# dbt SA: read from all BQ datasets, write to staging and mart
resource "google_bigquery_dataset_iam_member" "dbt_raw_read" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "dbt_staging_write" {
  dataset_id = google_bigquery_dataset.staging.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "dbt_mart_write" {
  dataset_id = google_bigquery_dataset.mart.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

# dbt SA also needs BQ job creation permission to run queries
resource "google_project_iam_member" "dbt_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dbt.email}"
}

# dbt SA needs to read GCS for external tables
resource "google_storage_bucket_iam_member" "dbt_raw_read" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.dbt.email}"
}

# Kestra SA: invoke Cloud Run jobs
resource "google_project_iam_member" "kestra_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.kestra.email}"
}

# ============================================================
# SECRET MANAGER — secure credential storage
# ============================================================

# We create empty secret containers now
# The actual values are added manually after terraform apply
# This way secrets never appear in Terraform code or state

resource "google_secret_manager_secret" "gcp_project_id" {
  secret_id = "citybikes-gcp-project-id"
  replication {
    auto {}
  }
  labels = {
    project = "citybikes-de"
  }
}

resource "google_secret_manager_secret" "citybikes_networks" {
  secret_id = "citybikes-networks"
  replication {
    auto {}
  }
  labels = {
    project = "citybikes-de"
  }
}

# Allow ingestion SA to read secrets
resource "google_secret_manager_secret_iam_member" "ingestion_project_id" {
  secret_id = google_secret_manager_secret.gcp_project_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ingestion.email}"
}

resource "google_secret_manager_secret_iam_member" "ingestion_networks" {
  secret_id = google_secret_manager_secret.citybikes_networks.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ingestion.email}"
}
