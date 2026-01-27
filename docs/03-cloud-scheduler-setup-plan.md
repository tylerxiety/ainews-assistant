# Cloud Scheduler Setup Plan

**Overall Progress:** `100%` ✅

## TLDR
Set up Google Cloud Scheduler to automatically trigger the newsletter processing endpoint every 6 hours. This enables the system to autonomously fetch and process new AINews issues without manual intervention.

## Critical Decisions
- **Trigger Strategy**: HTTP trigger to Cloud Run `/process-latest` endpoint - Simple, direct integration without additional infrastructure
- **Schedule Frequency**: Every 6 hours (`0 */6 * * *`) - Balances freshness with cost/resource efficiency per PROJECT-BRIEF.md
- **RSS Feed Discovery**: `/process-latest` endpoint auto-discovers the latest newsletter URL from `https://news.smol.ai/rss.xml` - Avoids hardcoding URLs in scheduler
- **Authentication**: Use Cloud Run service account with invoker permissions - Secure invocation while allowing scheduler access

## Tasks:

- [x] 🟩 **Step 1: Create Backend Endpoint for Scheduled Processing**
  - [x] 🟩 Add `/process-latest` endpoint to `main.py` that fetches the latest newsletter URL from RSS feed
  - [x] 🟩 Implement RSS feed parsing to discover the most recent issue URL from `https://news.smol.ai/rss.xml`
  - [x] 🟩 Add logic to skip processing if the issue already exists in Supabase
  - [x] 🟩 Test the endpoint locally ✓ Tested: `processing` on new issue, `skipped` on duplicate

- [x] 🟩 **Step 2: Deploy Updated Backend**
  - [x] 🟩 Commit and push the new endpoint code
  - [x] 🟩 Trigger GitHub Actions CI/CD pipeline ✓ Run #21213507424 succeeded
  - [x] 🟩 Verify `/process-latest` endpoint is accessible on Cloud Run ✓ Returns `skipped` for existing issue

- [x] 🟩 **Step 3: Create Cloud Scheduler Job**
  - [x] 🟩 Enable Cloud Scheduler API in GCP project
  - [x] 🟩 Create service account `scheduler-invoker@gen-lang-client-0104465868.iam.gserviceaccount.com`
  - [x] 🟩 Grant Cloud Run Invoker role to the service account
  - [x] 🟩 Create scheduler job `newsletter-processor-trigger`:
    - Region: `us-central1`
    - Schedule: `0 */6 * * *` (every 6 hours at minute 0, UTC)
    - Target: HTTP POST to `https://newsletter-processor-872179428244.us-central1.run.app/process-latest`
    - Auth: OIDC token with service account

- [x] 🟩 **Step 4: Test and Verify**
  - [x] 🟩 Manually trigger the scheduler job to test
  - [x] 🟩 Check Cloud Run logs for successful invocation
  - [x] 🟩 Verified RSS discovery working (found latest: `https://news.smol.ai/issues/26-01-20-not-much/`)
  - [x] 🟩 ⚠️ **Known Issue**: Background tasks may be killed when Cloud Run instance scales down (see notes below)

- [x] 🟩 **Step 5: Documentation & Monitoring**
  - [x] 🟩 Update `docs/mvp-implementation-plan.md` to mark Cloud Scheduler as complete
  - [x] 🟩 Document scheduler job details in this plan
  - [ ] 🟥 (Optional) Set up Cloud Monitoring alert for scheduler failures

## Known Issue: Cloud Run Background Task Limitation

⚠️ **Problem**: Cloud Run may shut down instances after the HTTP response is sent, killing in-progress background tasks. For large newsletters (798 segments), processing was interrupted.

**Solutions** (for future implementation):
1. **Increase Cloud Run min instances**: Keep at least 1 instance always running
2. **Use Cloud Tasks**: Queue processing as a separate task with longer timeout
3. **Synchronous processing**: Wait for processing to complete before responding (requires increasing scheduler timeout)
4. **Use Cloud Run Jobs**: Trigger a Cloud Run Job instead of HTTP endpoint for long-running tasks

For MVP, the current setup works for smaller newsletters. Large newsletters may need manual processing or one of the above solutions.

## GCP Commands Reference

```bash
# 1. Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com --project=gen-lang-client-0104465868

# 2. Create service account
gcloud iam service-accounts create scheduler-invoker \
  --display-name="Cloud Scheduler Invoker" \
  --project=gen-lang-client-0104465868

# 3. Grant Cloud Run invoker role
gcloud run services add-iam-policy-binding newsletter-processor \
  --member="serviceAccount:scheduler-invoker@gen-lang-client-0104465868.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1 \
  --project=gen-lang-client-0104465868

# 4. Create the scheduler job
gcloud scheduler jobs create http newsletter-processor-trigger \
  --location=us-central1 \
  --schedule="0 */6 * * *" \
  --uri="https://newsletter-processor-872179428244.us-central1.run.app/process-latest" \
  --http-method=POST \
  --oidc-service-account-email="scheduler-invoker@gen-lang-client-0104465868.iam.gserviceaccount.com" \
  --oidc-token-audience="https://newsletter-processor-872179428244.us-central1.run.app" \
  --project=gen-lang-client-0104465868

# 5. Manually trigger to test
gcloud scheduler jobs run newsletter-processor-trigger \
  --location=us-central1 \
  --project=gen-lang-client-0104465868

# 6. View scheduler job status
gcloud scheduler jobs describe newsletter-processor-trigger \
  --location=us-central1 \
  --project=gen-lang-client-0104465868
```

## Endpoint Implementation (Completed)

The `/process-latest` endpoint:
1. Fetches the RSS feed from `https://news.smol.ai/rss.xml`
2. Parses the most recent entry's URL
3. Checks if this URL already exists in `issues` table
4. If not exists, triggers background processing
5. Returns status: `skipped` (already processed), `processing` (started), or `no_new_issue` (RSS fetch failed)

## Output Location

This plan is saved to `docs/cloud-scheduler-setup-plan.md`.

