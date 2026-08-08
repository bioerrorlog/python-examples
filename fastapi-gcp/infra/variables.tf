variable "project_id" {
  description = "デプロイ先の Google Cloud プロジェクト ID"
  type        = string
}

variable "region" {
  description = "Cloud Run / Artifact Registry のリージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "service_name" {
  description = "Cloud Run サービス名（Artifact Registry のイメージ名にも使う）"
  type        = string
  default     = "fastapi-gcp"
}

variable "repository_id" {
  description = "Artifact Registry の Docker リポジトリ ID"
  type        = string
  default     = "fastapi-gcp"
}

variable "image_tag" {
  description = "デプロイするコンテナイメージのタグ"
  type        = string
  default     = "latest"
}

variable "iap_members" {
  description = <<-EOT
    IAP 経由でアプリにアクセスできる IAM プリンシパル。
    例: ["user:you@gmail.com", "group:dev@example.com", "domain:example.com"]
  EOT
  type        = list(string)

  validation {
    condition     = length(var.iap_members) > 0
    error_message = "少なくとも 1 つのプリンシパルを指定してください。空の場合、誰もアプリにアクセスできません。"
  }
}

variable "max_instance_count" {
  description = "Cloud Run の最大インスタンス数"
  type        = number
  default     = 3
}
