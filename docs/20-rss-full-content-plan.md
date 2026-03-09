# RSS Full Content Fetching Plan

**Overall Progress:** `100%`

## TLDR
Substack paywalls unauthenticated fetches of Latent Space posts, truncating content at "Top Tweets". Switched from page-fetching to RSS `content:encoded` as primary content source. Added `connect.sid` cookie fallback: when RSS content is truncated (detected via "Read more" link pattern), re-fetches the same RSS feed with `connect.sid` cookie for full content.

**Update (2026-02-19):** Switched RSS feed from `latent.space/feed?section=ainews` back to `news.smol.ai/rss.xml`. The `connect.sid` cookie expired within hours (worked at Feb 14 08:52, dead by 12:00), causing all issues from Feb 15+ to be processed with truncated content. The smol.ai feed returns full 115K+ char content without authentication. Reprocessed the two affected issues (Sonnet 4.6, Qwen 3.5) and deleted the old broken latent.space entries.

**Update (2026-03-09):** `news.smol.ai` stopped publishing again. Switched to Latent Space Substack RSS with a private subscriber token: `latent.space/feed?token=...`. The token (from the Substack private podcast RSS feature) also works on the newsletter feed, providing full content without any cookie auth. Added `titleFilter: "^\[AINews\]"` to select only AINews posts. Removed `authCookieName`/`authCookieEnv` — no longer needed. Also added the same token to the `latent_space` source feed.

## Critical Decisions
- **Use RSS `content:encoded` as primary content source** — RSS is stable; page fetching was broken by paywall
- **`connect.sid` cookie for paywall bypass** — `substack.sid` only works on `.substack.com`, NOT on custom domains like `www.latent.space`; `connect.sid` is the correct cookie for custom Substack domains
- **Re-fetch RSS feed (not page)** — cookie-authenticated RSS feed returns full `content:encoded` (70-96K chars); no HTML page parsing needed
- **Switched back to `news.smol.ai/rss.xml`** — the smol.ai feed no longer redirects to latent.space login (was an issue on Feb 14); provides full content without auth. The `connect.sid` cookie expires in hours, making the latent.space feed unreliable.
- **Switched to Latent Space private token RSS (2026-03-09)** — `news.smol.ai` stopped publishing again. Discovered that the Substack private podcast RSS token also works on the newsletter feed, providing full content without cookie auth. URL: `latent.space/feed?token=...` with `titleFilter: "^\[AINews\]"`. No more cookie expiry issues.
- **Remove `_fetch_newsletter()` and `/process` endpoint** — obsolete; `/process-latest?force=true` covers reprocessing
- **RSS entry title passthrough** — RSS `content:encoded` has no `<title>` tag; use `entry.title` from feed metadata
- **Pause prod scheduler** — prod/dev share one Supabase DB; dev backend gets fixes first

## Tasks

- [x] 🟩 **Step 1: Pause prod scheduler**
  - [x] 🟩 `gcloud scheduler jobs pause newsletter-processor-trigger --location=us-central1`

- [x] 🟩 **Step 2: Switch to RSS content as primary source**
  - [x] 🟩 Renamed `fetch_latest_newsletter_url()` → `fetch_latest_newsletter()`, returns `tuple[str, str, str]` (url, title, html_content)
  - [x] 🟩 Added `_fetch_rss_entry()` helper that parses feed and returns `(url, title, html_content)` per entry
  - [x] 🟩 Extract `entry.content[0].value` with `entry.summary` fallback

- [x] 🟩 **Step 3: Add truncation detection + cookie fallback**
  - [x] 🟩 Detect truncation via regex: `<a href="...">Read more</a>` at end of content
  - [x] 🟩 When truncated, re-fetch RSS feed with `connect.sid` cookie from `SUBSTACK_CONNECT_SID` env var
  - [x] 🟩 Log warning when cookie not set, process truncated content as fallback

- [x] 🟩 **Step 4: Title fix + code cleanup**
  - [x] 🟩 Pass RSS entry title through pipeline: `fetch_latest_newsletter()` → `process_newsletter()` → `_parse_newsletter()`
  - [x] 🟩 Remove `_fetch_newsletter()` method
  - [x] 🟩 Remove `/process` endpoint, `ProcessRequest`, and unused imports

- [x] 🟩 **Step 5: Update `/process-latest` endpoint**
  - [x] 🟩 Unpack 3-tuple `(url, title, html_content)` from `fetch_latest_newsletter()`
  - [x] 🟩 Added `entry_index` query param for reprocessing specific RSS entries

- [x] 🟩 **Step 6: Infrastructure**
  - [x] 🟩 Fixed `deploy-backend-dev.yml` env var escaping (`^||^` delimiter for ALLOWED_ORIGINS)
  - [x] 🟩 Added `SUBSTACK_CONNECT_SID` to deploy workflow and GitHub secrets
  - [x] 🟩 Set `SUBSTACK_CONNECT_SID` env var on Cloud Run dev service
  - [x] 🟩 Created `newsletter-processor-dev-trigger` scheduler (6-hour schedule)

- [x] 🟩 **Step 7: Switch RSS feed back to smol.ai (2026-02-19)**
  - [x] 🟩 Changed `rssUrl` in `config.yaml` from `latent.space/feed?section=ainews` to `news.smol.ai/rss.xml`
  - [x] 🟩 Deployed to dev via CI
  - [x] 🟩 Reprocessed Sonnet 4.6 (`entry_index=1`) → 31 groups, 158 segments
  - [x] 🟩 Reprocessed Qwen 3.5 (`entry_index=2`) → 24 groups, 115 segments
  - [x] 🟩 Deleted old broken `latent.space` issues (`68b8e3c2`, `55eabc1d`)

- [x] 🟩 **Step 8: Switch to Latent Space private token RSS (2026-03-09)**
  - [x] 🟩 `news.smol.ai` stopped publishing again
  - [x] 🟩 Discovered private podcast RSS token (`755e0227-...`) also works on newsletter feed
  - [x] 🟩 Changed `ainews` rssUrl to `latent.space/feed?token=...` with `titleFilter: "^\[AINews\]"`
  - [x] 🟩 Added same token to `latent_space` source feed
  - [x] 🟩 Removed `authCookieName`/`authCookieEnv` — cookie auth no longer needed
  - [x] 🟩 Updated tests in `test_multi_source.py`
  - [x] 🟩 Deployed and batch-processed entries 0–10 from feed

## Testing (Required)

### Approach
API testing via curl against the dev backend endpoint.

### Test Scenarios
- [x] 🟩 Scenario 1: `process-latest?force=true&entry_index=0` → completed, 84K chars, 137 segments, 23 topic groups
- [x] 🟩 Scenario 2: `process-latest?force=true&entry_index=1` → completed, 71K chars, 132 segments, 22 topic groups
- [x] 🟩 Scenario 3: Correct titles: "[AINews] Why OpenAI Should Build Slack" and "[AINews] new Gemini 3 Deep Think..."
- [ ] 🟥 Scenario 4: Run `/process-latest` without `force` → `status: "skipped"` (not yet tested)
- [ ] 🟥 Scenario 5: Verify cookie fallback triggers when content is truncated (depends on Substack paywall timing)

### Acceptance Criteria
- [x] Both latest issues have 130+ segments covering all sections (not truncated at "Top Tweets")
- [x] Issue titles match RSS entry titles (not extracted from HTML body)
- [x] Dev scheduler job exists, prod scheduler paused
- [x] `SUBSTACK_CONNECT_SID` set in Cloud Run env + GitHub secret + deploy workflow
- [x] No remaining references to `_fetch_newsletter()` in codebase
