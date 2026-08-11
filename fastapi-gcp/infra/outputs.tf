output "service_url" {
  description = "Cloud Run service URL, protected by IAP sign-in"
  value       = google_cloud_run_v2_service.app.uri
}

output "image" {
  description = "Container image deployed to Cloud Run"
  value       = local.image
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL to push images to"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "runtime_service_account" {
  description = "Runtime service account of the Cloud Run service"
  value       = google_service_account.run.email
}

output "client_service_account" {
  description = "Service account to impersonate when calling the service programmatically"
  value       = google_service_account.client.email
}

output "iap_service_agent" {
  description = "IAP service agent that invokes the Cloud Run service"
  value       = google_project_service_identity.iap.email
}

output "storage_bucket" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.app.name
}
