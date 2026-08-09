#!/usr/bin/env bash
# Build the app image, push it to Artifact Registry, and deploy it to Cloud Run.
set -euo pipefail

PROJECT_ID="your-gcp-project-id"
REGION="asia-northeast1"
SERVICE="fastapi-gcp"
REPOSITORY="fastapi-gcp"

IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE:latest"
APP_DIR="$(dirname "$0")/../app"

# Cloud Run only runs linux/amd64, so the platform is pinned for Apple Silicon.
docker build --platform linux/amd64 -t "$IMAGE" "$APP_DIR"
docker push "$IMAGE"

gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT_ID"
