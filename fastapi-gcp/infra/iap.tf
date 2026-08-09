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
# This role binds on the IAP resource, not on the Cloud Run service itself:
# the Cloud Run IAM API rejects roles/iap.httpsResourceAccessor.
resource "google_iap_web_cloud_run_service_iam_member" "iap_accessor" {
  for_each = toset(var.iap_members)

  project                = var.project_id
  location               = google_cloud_run_v2_service.app.location
  cloud_run_service_name = google_cloud_run_v2_service.app.name
  role                   = "roles/iap.httpsResourceAccessor"
  member                 = each.value
}

# Identity used to call the service programmatically.
resource "google_service_account" "client" {
  project      = var.project_id
  account_id   = "${var.service_name}-client"
  display_name = "Programmatic client for ${var.service_name}"
}

resource "google_iap_web_cloud_run_service_iam_member" "client_iap_accessor" {
  project                = var.project_id
  location               = google_cloud_run_v2_service.app.location
  cloud_run_service_name = google_cloud_run_v2_service.app.name
  role                   = "roles/iap.httpsResourceAccessor"
  member                 = "serviceAccount:${google_service_account.client.email}"
}

# Principals allowed to impersonate the client service account and sign JWTs as it.
resource "google_service_account_iam_member" "client_token_creator" {
  for_each = toset(var.client_impersonators)

  service_account_id = google_service_account.client.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = each.value
}
