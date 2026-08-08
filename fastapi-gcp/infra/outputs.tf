output "service_url" {
  description = "Cloud Run サービスの URL（IAP のログインが必要）"
  value       = google_cloud_run_v2_service.app.uri
}

output "image" {
  description = "Cloud Run にデプロイされるコンテナイメージ"
  value       = local.image
}

output "artifact_registry_repository" {
  description = "docker push 先のリポジトリ URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "runtime_service_account" {
  description = "Cloud Run のランタイムサービスアカウント"
  value       = google_service_account.run.email
}

output "iap_service_agent" {
  description = "Cloud Run を呼び出す IAP のサービスエージェント"
  value       = google_project_service_identity.iap.email
}
