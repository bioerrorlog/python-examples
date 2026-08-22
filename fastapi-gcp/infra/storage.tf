resource "google_storage_bucket" "app" {
  project                     = var.project_id
  name                        = "${var.project_id}-${var.service_name}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  force_destroy = true
}
