terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.location
}

locals {
  datasets = {
    raw = {
      dataset_id  = "fraud_project_raw"
      description = "Raw Kaggle IEEE-CIS Fraud Detection tables and model support outputs."
    }
    staging = {
      dataset_id  = "fraud_project_staging"
      description = "Typed and standardized dbt staging models."
    }
    intermediate = {
      dataset_id  = "fraud_project_intermediate"
      description = "Joined and feature-engineered dbt intermediate models."
    }
    mart = {
      dataset_id  = "fraud_project_mart"
      description = "Fraud analytics marts, model predictions, and quality outputs."
    }
    powerbi = {
      dataset_id  = "fraud_project_powerbi"
      description = "Power BI DirectQuery reporting layer."
    }
  }
}

resource "google_bigquery_dataset" "fraud_project" {
  for_each = local.datasets

  dataset_id                 = each.value.dataset_id
  description                = each.value.description
  location                   = var.location
  delete_contents_on_destroy = false

  labels = {
    project = "fraud_project"
    layer   = each.key
  }
}
