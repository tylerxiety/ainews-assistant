# Cloud Scheduler Setup Plan

**Overall Progress:** `20%`

## TLDR
Set up Google Cloud Scheduler to automatically trigger the newsletter processing endpoint every 6 hours. This enables the system to autonomously fetch and process new AINews issues without manual intervention.

## Critical Decisions
- **Trigger Strategy**: HTTP trigger to Cloud Run `/process` endpoint - Simple, direct integration without additional infrastructure
- **Schedule Frequency**: Every 6 hours (`0 */6 * * *`) - Balances freshness with cost/resource efficiency per PROJECT-BRIEF.md
- **RSS Feed Discovery**: Create a new `/process-latest` endpoint to auto-discover the latest newsletter URL from RSS feed - Avoids hardcoding URLs in scheduler
- **Authentication**: Use Cloud Run service account with invoker permissions - Secure invocation while allowing scheduler access

## Tasks:

- [x] 🟩 **Step 1: Create Backend Endpoint for Scheduled Processing**
  - [x] 🟩 Add `/process-latest` endpoint to `main.py` that fetches the latest newsletter URL from RSS feed
  - [x] 🟩 Implement RSS feed parsing to discover the most recent issue URL from `https://buttondown.com/ainews/rss`
  - [x] 🟩 Add logic to skip processing if the issue already exists in Supabase
  - [x] 🟩 Test the endpoint locally ✓ Tested: `processing` on new issue, `skipped` on duplicate

- [x] 🟩 **Step 2: Deploy Updated Backend**
  - [ ] 🟥 Commit and push the new endpoint code
  - [ ] 🟥 Trigger GitHub Actions CI/CD pipeline (or run `deploy.sh` manually)
  - [ ] 🟥 Verify `/process-latest` endpoint is accessible on Cloud Run

- [ ] 🟥 **Step 3: Create Cloud Scheduler Job**
  - [ ] 🟥 Enable Cloud Scheduler API in GCP project
  - [ ] 🟥 Create a service account for scheduler (or use existing compute service account)
  - [ ] 🟥 Grant Cloud Run Invoker role to the service account
  - [ ] 🟥 Create the scheduler job with:
    - Name: `newsletter-processor-trigger`
    - Region: `us-central1`
    - Schedule: `0 */6 * * *` (every 6 hours at minute 0)
    - Target: HTTP POST to `https://newsletter-processor-872179428244.us-central1.run.app/process-latest`
    - Auth: OIDC token with service account

- [ ] 🟥 **Step 4: Test and Verify**
  - [ ] 🟥 Manually trigger the scheduler job to test
  - [ ] 🟥 Check Cloud Run logs for successful processing
  - [ ] 🟥 Verify new issue appears in Supabase (if new issue was available)
  - [ ] 🟥 Confirm audio files are generated in GCS

- [ ] 🟥 **Step 5: Documentation & Monitoring**
  - [ ] 🟥 Update `docs/mvp-implementation-plan.md` to mark Cloud Scheduler as complete
  - [ ] 🟥 Document scheduler job details in README or docs
  - [ ] 🟥 (Optional) Set up Cloud Monitoring alert for scheduler failures

## GCP Commands Reference

```bash
# 1. Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com --project=gen-lang-client-0104465868

# 2. Create service account (optional, can use default compute SA)
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
```

## Endpoint Implementation Notes

The `/process-latest` endpoint should:
1. Fetch the RSS feed from `https://buttondown.com/ainews/rss`
2. Parse the most recent entry's URL
3. Check if this URL already exists in `issues` table
4. If not exists, call the existing `process_newsletter()` logic
5. Return status: `skipped` (already processed) or `processing` (started)

```python
@app.post("/process-latest")
async def process_latest_newsletter(background_tasks: BackgroundTasks):
    """
    Discover and process the latest newsletter from RSS feed.
    Called by Cloud Scheduler every 6 hours.
    """
    # 1. Fetch RSS to get latest URL
    # 2. Check if already processed
    # 3. If new, trigger processing
    pass
```

## Output Location

This plan is saved to `docs/cloud-scheduler-setup-plan.md`.
