terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source = "hashicorp/google"
      # cloud_run_v2_service の iap_enabled は 6.14 以降で利用可能
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }

  # 複数人・CI から実行する場合は GCS バックエンドを有効化する
  # backend "gcs" {
  #   bucket = "<tfstate-bucket>"
  #   prefix = "fastapi-gcp"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
