# CI/CD Setup Guide

This guide explains how to configure automatic deployments for your project.

## 1. Vercel (Frontend)

The frontend is configured to deploy to Vercel.

### Configuration
A `vercel.json` file has been added to the `frontend/` directory to specify the build settings.

### Setup Steps
1.  Go to the [Vercel Dashboard](https://vercel.com/dashboard).
2.  Add a **New Project** and import this GitHub repository.
3.  **Important**: In the project settings:
    *   **Root Directory**: Select `frontend`.
    *   Vercel should automatically detect the `vercel.json` or Vite framework settings.
4.  **Environment Variables**:
    *   Add `VITE_SUPABASE_URL`
    *   Add `VITE_SUPABASE_ANON_KEY`
5.  Deploy. Future pushes to `main` will trigger automatic deployments.

## 2. Supabase (Database Migrations)

The database migrations are configured to deploy via GitHub Actions.

### Setup Steps
1.  Go to your GitHub Repository > **Settings** > **Secrets and variables** > **Actions**.
2.  Add the following **Repository Secrets**:
    *   `SUPABASE_PROJECT_ID`: Your Supabase Project Reference.
    *   `SUPABASE_DB_PASSWORD`: Your Supabase Database Password.
    *   `SUPABASE_ACCESS_TOKEN`: A Personal Access Token from Supabase.

## 3. Backend (Cloud Run)

The backend is configured to deploy via GitHub Actions using Google Application Default Credentials (ADC) concepts, which means we pass the Service Account Key to the runner, and the Cloud Run service runs with that identity.

### Setup Steps
In your GitHub Repository > **Settings** > **Secrets and variables** > **Actions**, add:

1.  `GCP_PROJECT_ID`: Your Google Cloud Project ID.
2.  `GCP_SA_KEY`: The JSON content of your Service Account Key (`service-account-key.json`).
3.  `GCP_SA_EMAIL` (Optional/Good Practice): The email of the service account (e.g., `ainews-processor@...`). *I added this to the workflow to ensure the service runs as the correct user.*
4.  `SUPABASE_URL`: Your Supabase URL.
5.  `SUPABASE_SERVICE_KEY`: Your Supabase Service Role Key (the `service_role` key, NOT the anon key).
6.  `GCS_BUCKET_NAME`: Your Storage Bucket name.

### Why no Secret Manager?
Since you are using ADC, you are likely authenticating comfortably with keys.
*   **ADC** handles the Google part (GCS, Vertex AI).
*   **Supabase** is external. We simply pass the `SUPABASE_SERVICE_KEY` environment variable directly to Cloud Run via the GitHub Action. This avoids the complexity of configuring Google Secret Manager.

## Summary of Triggers

*   **Change in `frontend/`**: Vercel deploys.
*   **Change in `backend/`**: Backend workflow runs and deploys to Cloud Run.
*   **Change in `supabase/migrations/`**: Supabase workflow runs.
