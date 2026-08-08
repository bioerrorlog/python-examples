locals {
  services = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iap.googleapis.com",
    "cloudbuild.googleapis.com",
  ]

  image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/${var.service_name}:${var.image_tag}"
}

resource "google_project_service" "this" {
  for_each = toset(local.services)

  project = var.project_id
  service = each.value

  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = "Container images for ${var.service_name}"

  depends_on = [google_project_service.this]
}

# Dedicated runtime service account; the default Compute Engine SA is too privileged.
resource "google_service_account" "run" {
  project      = var.project_id
  account_id   = "${var.service_name}-run"
  display_name = "Runtime service account for ${var.service_name}"
}

resource "google_project_iam_member" "run_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.run.email}"
}

resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  name     = var.service_name
  location = var.region

  deletion_protection = false

  # With the IAP direct integration, requests reach Cloud Run through IAP,
  # so ingress stays open and access is controlled by IAP + run.invoker.
  ingress = "INGRESS_TRAFFIC_ALL"

  iap_enabled = true

  template {
    service_account = google_service_account.run.email

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instance_count
    }

    containers {
      image = local.image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 0
        period_seconds        = 5
        timeout_seconds       = 3
        failure_threshold     = 6
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.this]
}

# IAP authenticates users and forwards only authenticated requests to Cloud Run.
# roles/iap.httpsResourceAccessor decides who may sign in with a Google account,
# roles/run.invoker on the IAP service agent lets IAP call the Cloud Run service.
resource "google_project_service_identity" "iap" {
  provider = google-beta

  project = var.project_id
  service = "iap.googleapis.com"

  depends_on = [google_project_service.this]
}

resource "google_cloud_run_v2_service_iam_member" "iap_invoker" {
  project  = var.project_id
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_project_service_identity.iap.email}"
}

# Google accounts allowed to pass the IAP sign-in screen.
resource "google_cloud_run_v2_service_iam_member" "iap_accessor" {
  for_each = toset(var.iap_members)

  project  = var.project_id
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/iap.httpsResourceAccessor"
  member   = each.value
}
