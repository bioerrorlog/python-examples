// IAP がユーザー認証を行い、認証済みリクエストのみを Cloud Run に転送する。
// 「誰が Google アカウントでログインできるか」は roles/iap.httpsResourceAccessor、
// 「IAP が Cloud Run を呼べるか」は IAP サービスエージェントへの roles/run.invoker で決まる。

# IAP のサービスエージェント（service-<PROJECT_NUMBER>@gcp-sa-iap.iam.gserviceaccount.com）を明示的に作成する
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

# IAP のログイン画面を通過できる Google アカウント
resource "google_cloud_run_v2_service_iam_member" "iap_accessor" {
  for_each = toset(var.iap_members)

  project  = var.project_id
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/iap.httpsResourceAccessor"
  member   = each.value
}
