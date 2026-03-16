terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Remote state stored in GCS
  # This means Terraform's record of what it created is stored in the cloud
  # not on your laptop — so it's never lost and can be shared
  backend "gcs" {
    # These values are filled in during terraform init
    # See the init command below — we pass them as -backend-config flags
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
