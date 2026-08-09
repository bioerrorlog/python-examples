#!/usr/bin/env bash
# One-time setup: sign in to Google Cloud and let docker push to Artifact Registry.
set -euo pipefail

PROJECT_ID="my-project-id"
REGION="asia-northeast1"

# User credentials for gcloud/terraform.
gcloud auth login

# Application Default Credentials, used by terraform and the e2e client.
gcloud auth application-default login

gcloud config set project "$PROJECT_ID"

# Register gcloud as the docker credential helper for the registry.
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
