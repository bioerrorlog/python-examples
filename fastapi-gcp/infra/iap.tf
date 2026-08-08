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
