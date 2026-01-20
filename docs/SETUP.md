# Setup Guide

## Quick Start

### 1. Clone and Install

```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
uv sync
```

### 2. Configure Environment Variables

#### Frontend (.env.local)
```bash
cd frontend
cp .env.example .env.local
# Edit with your Supabase credentials
```

#### Backend (.env)
```bash
cd backend
cp .env.example .env
# Edit with your GCP and Supabase credentials
```

### 3. Set Up Database

```bash
# Option 1: Using Supabase CLI
cd supabase
npx supabase init
npx supabase db push

# Option 2: Manual (via Supabase Dashboard)
# Copy contents of supabase/migrations/001_initial_schema.sql
# Paste into SQL Editor in Supabase Dashboard
# Run the query
```

### 4. Run Locally

```bash
# Terminal 1: Backend
cd backend
uv run uvicorn main:app --reload --port 8080

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Google Cloud Setup

### Enable Required APIs

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable texttospeech.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
```

### Create Storage Bucket

```bash
gsutil mb -l us-central1 gs://YOUR_BUCKET_NAME

# Make bucket publicly readable (for audio URLs)
gsutil iam ch allUsers:objectViewer gs://YOUR_BUCKET_NAME
```

### Service Account (for local development)

```bash
# Create service account
gcloud iam service-accounts create newsletter-processor \
  --display-name="Newsletter Processor"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:newsletter-processor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:newsletter-processor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:newsletter-processor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtts.user"

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=newsletter-processor@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
```

## Testing the Pipeline

### 1. Process a Newsletter Issue

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"}'
```

Response:
```json
{
  "status": "processing",
  "issue_id": "uuid-here",
  "message": "Newsletter processing started"
}
```

### 2. Check Processing Status

```bash
curl http://localhost:8080/issues/{issue_id}
```

### 3. Verify in Supabase Dashboard

- Go to Table Editor
- Check `issues` table: Should see new row with title and URL
- Check `segments` table: Should see multiple rows with audio URLs
- Verify `audio_url` fields point to GCS

### 4. Test Frontend

1. Open http://localhost:5173
2. Should see issue list (once implemented)
3. Click on issue to view player
4. Audio should play

## Deployment

### Backend to Cloud Run

```bash
cd backend

gcloud run deploy newsletter-processor \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SUPABASE_URL=$SUPABASE_URL,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY,GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_REGION=us-central1,GCS_BUCKET_NAME=$GCS_BUCKET_NAME
```

### Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard:
# - VITE_SUPABASE_URL
# - VITE_SUPABASE_ANON_KEY
# - VITE_CLICKUP_LIST_ID
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.11+)
- Verify virtual environment is activated
- Check environment variables in `.env`

### GCP Authentication Errors
- Verify `GOOGLE_APPLICATION_CREDENTIALS` is set
- Check service account has correct permissions
- Confirm APIs are enabled in GCP Console

### Supabase Connection Issues
- Verify `SUPABASE_URL` and keys are correct
- Check database is accessible (test in Supabase dashboard)
- Confirm migrations have been applied

### Frontend Build Errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check `.env.local` file exists
- Verify all environment variables start with `VITE_`

### Audio Generation Fails
- Check GCS bucket exists and is accessible
- Verify TTS API is enabled
- Confirm text is not too long (split into smaller segments if needed)

## Next Steps

After successful setup:

1. Implement frontend components (Issue list, Player view)
2. Add audio sync logic
3. Implement ClickUp integration
4. Configure PWA settings
5. Set up Cloud Scheduler for automatic processing
