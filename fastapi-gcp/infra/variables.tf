variable "project_id" {
  description = "Google Cloud project to deploy into"
  type        = string
}

variable "region" {
  description = "Region for Cloud Run and Artifact Registry"
  type        = string
  default     = "asia-northeast1"
}

variable "service_name" {
  description = "Cloud Run service name, also used as the container image name"
  type        = string
  default     = "fastapi-gcp"
}

variable "repository_id" {
  description = "Artifact Registry Docker repository ID"
  type        = string
  default     = "fastapi-gcp"
}

variable "image_tag" {
  description = "Tag of the container image to deploy"
  type        = string
  default     = "latest"
}

variable "iap_members" {
  description = <<-EOT
    IAM principals allowed to reach the app through IAP.
    Example: ["user:you@gmail.com", "group:dev@example.com", "domain:example.com"]
  EOT
  type        = list(string)

  validation {
    condition     = length(var.iap_members) > 0
    error_message = "Specify at least one principal, otherwise nobody can access the app."
  }
}

variable "max_instance_count" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 3
}
