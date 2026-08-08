locals {
  services = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iap.googleapis.com",
    "cloudbuild.googleapis.com", # gcloud builds submit でイメージをビルドするため
  ]
}

resource "google_project_service" "this" {
  for_each = toset(local.services)

  project = var.project_id
  service = each.value

  # terraform destroy 時に API まで無効化すると他リソースに波及するため無効化しない
  disable_on_destroy = false
}
