#!/bin/bash
set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="us-central1"
SERVICE_NAME="newsletter-processor"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Environment variables
# TODO: Replace these with your actual values or use Secret Manager
SUPABASE_URL="${SUPABASE_URL:-https://your-project.supabase.co}"
GCS_BUCKET_NAME="${GCS_BUCKET_NAME:-your-gcs-bucket-name}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.0-flash-exp}"
MAX_CONCURRENT_SEGMENTS="${MAX_CONCURRENT_SEGMENTS:-5}"
TTS_VOICE_NAME="${TTS_VOICE_NAME:-en-US-Chirp3-HD-Aoede}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://your-frontend-domain.vercel.app}"

echo "Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo "Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "\
ENVIRONMENT=production,\
SUPABASE_URL=${SUPABASE_URL},\
GCP_PROJECT_ID=${PROJECT_ID},\
GCP_REGION=${REGION},\
GCS_BUCKET_NAME=${GCS_BUCKET_NAME},\
GEMINI_MODEL=${GEMINI_MODEL},\
MAX_CONCURRENT_SEGMENTS=${MAX_CONCURRENT_SEGMENTS},\
TTS_VOICE_NAME=${TTS_VOICE_NAME},\
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}" \
  --update-secrets="SUPABASE_SERVICE_KEY=supabase_service_key:latest" \
  --timeout 300 \
  --memory 1Gi \
  --cpu 1

echo "Deployment complete!"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)'

echo ""
echo "NOTE: Make sure you have created the secret in Secret Manager:"
echo "  gcloud secrets create supabase_service_key --data-file=- <<< 'your-service-key'"
echo "  gcloud secrets add-iam-policy-binding supabase_service_key \\"
echo "    --member='serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com' \\"
echo "    --role='roles/secretmanager.secretAccessor'"
