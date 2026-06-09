# Project Instructions

## Overview
AI News Assistant - PWA that converts AI/ML newsletters (8 sources including AINews, The Batch, Import AI, and more) into listenable audio with visual sync, voice commands/Q&A, bilingual support (EN/ZH), and tap-to-bookmark to ClickUp. Auto-processed every 6 hours via Cloud Scheduler.

## Tech Stack
- **Frontend**: Vite + React 19 + TypeScript + plain CSS (PWA on Vercel), lucide-react icons
- **Backend**: Python + FastAPI (Cloud Run)
- **Database**: Supabase (Postgres) | **Storage**: GCS (audio files)
- **TTS**: Google Cloud TTS (Chirp 3 HD Aoede for EN, cmn-CN for ZH)
- **AI**: Gemini models (text cleaning, Q&A, voice mode)
- **Voice Mode**: Gemini Live API via backend WebSocket proxy, client-side VAD (@ricky0123/vad-web)
- **i18n**: Custom React context + JSON locale files (en/zh)
- **Config**: Centralized `config.yaml` (shared by frontend/backend)

## Key Decisions
- **Voice mode**: Tap-to-enable hands-free commands (play/pause/next/previous/bookmark/rewind/forward) and Q&A via Gemini Live. Backend WebSocket proxy for iOS Safari compatibility. Client-side VAD pauses newsletter instantly on speech.
- **Voice mode session lifecycle**: `sessionTimeoutMs` is for proactive WebSocket refresh (about 14 minutes, due to Gemini Live API's 15 min limit), not shutdown. Timeout must trigger socket close + auto-reconnect with resumption handle, so long-running sessions continue without manual re-enable.
- **Fallback Q&A**: MediaRecorder + server-side Gemini when voice mode is off
- **Per-segment audio**: One TTS call per segment; topic groups are for UI/ordering only
- **Single `<audio>` element**: Newsletter playback only; Q&A audio plays via AudioContext
- **UI Architecture**: `Player.tsx` orchestrates state; `SegmentList` (content), `AudioBar` (controls), `SidePanel` (TOC + Q&A)
- **Bilingual content**: Separate `*_zh` columns in DB; skip segments without Chinese audio when UI is ZH
- **UI localization**: Simple JSON locale files with React context; persisted to localStorage; both EN/ZH voice commands always recognized
- **Multi-source newsletters**: 8 sources configured in `config.yaml` under `newsletterSources`. Each has its own RSS URL, optional auth cookie, and content filtering rules. `issues.source` column tracks origin; `NULL` = legacy ainews. The Batch uses bundle detection (`filterBundleOnly`) to skip individual articles. Two sources use `titleFilter` regex to select matching entries (AINews selects `[AINews]` posts; Last Week in AI skips podcast episodes). Source-specific junk text (ElevenLabs loader, Tongyi promo footer) is filtered in `_parse_newsletter`. Frontend shows filter tabs + colored source badges.
- **AINews source**: Uses Gmail API (`fetchMethod: "gmail"`) to fetch full-text AINews emails forwarded from `swyx+ainews@substack.com` to `tylerxiety@gmail.com`. OAuth2 credentials (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`) stored as env vars / GitHub secrets.
- **Offline reading**: `useOfflineDownload` hook pre-fetches issue data via `fetchIssueWithGroups`, letting the Workbox NetworkFirst SW cache Supabase responses (7-day expiration, 200 entries). Downloaded issue IDs tracked in localStorage. Download button in `IssueList.tsx` on processed issues. GCS bucket has CORS configured (`gsutil cors get gs://ainews-audio-prod`).

## Conventions

### Backend
- **Package manager**: `uv` — always run `cd backend && uv run <command>`
- Use `logging` module (not `print`), type hints for function signatures

### Frontend
- Functional components with hooks, strict typing (no `any`), proper useEffect cleanup
- Two-color palette (black + orange), lucide-react icons
- In `useVoiceMode`, session timeout handlers must refresh the socket (close/reconnect path) and must not call `stopVoiceMode()`; only explicit user toggle/off flow should fully stop voice mode.

### Post-Implementation
- After implementing a change, always run tests (`npm run test`, `uv run pytest`) and type checks (`npx tsc --noEmit`) before considering it done.
- For frontend UI changes, browser-test the actual behavior using Playwright.
- If all tests and verification pass, commit the change automatically — don't wait for the user to ask.

### General
- Keep solutions simple — don't over-engineer
- No debug code or TODOs in commits
- **All config in `/config.yaml`** — frontend imports via rollup-plugin-yaml, backend via PyYAML

### Testing
- **Unit tests** (CI runs these on push/PR to `dev` via `.github/workflows/test.yml`):
  ```bash
  cd backend && uv run pytest -v        # pytest, config in pyproject.toml
  cd frontend && npm run test            # vitest
  ```
- Backend shared fixtures live in `backend/tests/conftest.py` (e.g. `processor` fixture with mocked GCP/Supabase deps)
- **Manual/mobile testing** against ngrok tunnel (NOT dev server):
  ```bash
  cd frontend && VITE_API_URL="" npm run build
  cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8080
  ngrok http 8080
  ```
- No standalone test scripts in commits; temp scripts in `tests/tmp/` (delete before commit)

### Documentation
- Agent docs in `docs/` with numbered prefix, lowercase `docs/no-<feature-name>-plan.md` (e.g., `13-auth-plan.md`)

### Infrastructure
- GCP uses ADC — no explicit keys needed
- CLIs available: `gcloud`, `supabase`, `vercel`, `gh`
- Ask permission before create/modify/delete commands; read-only commands are fine

### Backend environments
Hackathon freeze ended; `dev` has been merged into `main`. The `dev` branch + `newsletter-processor-dev` Cloud Run service are kept as a staging environment for changes that need testing before `main`.

- **GCP project**: `ainews-assistant` (account: `tyler.ty.xie@gmail.com`)
- **Services**:
  - **Prod** — `newsletter-processor` at `https://newsletter-processor-sju3afmruq-uc.a.run.app`
    - Deployed by `.github/workflows/deploy-backend.yml` on push to `main`
    - Writes audio to `gs://ainews-audio-prod`
    - Uses `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GCS_BUCKET_NAME`
  - **Dev/staging** — `newsletter-processor-dev` at `https://newsletter-processor-dev-sju3afmruq-uc.a.run.app`
    - Deployed by `.github/workflows/deploy-backend-dev.yml` on push to `dev`
    - Writes audio to `gs://ainews-audio-dev`
    - Uses `SUPABASE_URL_DEV`, `SUPABASE_SERVICE_KEY_DEV`, `GCS_BUCKET_NAME_DEV`
- **Shared Supabase**: `SUPABASE_URL` and `SUPABASE_URL_DEV` currently point at the same project — the `_DEV` secrets exist to keep the deploy workflow uniform, not for DB isolation. Any prod and dev run writes into the same tables.
- **Buckets are split, not isolated**: dev and prod write to different GCS buckets, but Supabase `audio_url` columns store full URLs (`https://storage.googleapis.com/<bucket>/<path>`), so issues stay pinned to whichever bucket originally generated them. Recent multi-source content largely lives in `ainews-audio-dev` because the active scheduler hits the dev service. Do not delete or rename a bucket without first rewriting the `audio_url` / `audio_url_zh` rows in Supabase.
- **Vercel `VITE_API_URL`**:
  - `Production` → `newsletter-processor`
  - `Preview (dev)` → `newsletter-processor-dev`
  - Branch alias: `https://ainews-assistant-git-dev-tylers-projects-7e632143.vercel.app`
- **Schedulers** (only one runs at a time — both write into the shared Supabase):
  - `newsletter-processor-trigger` → prod `/process-latest` (AINews only) — **PAUSED**
  - `newsletter-dev-all` → dev `/process-all-latest` (all sources from `config.yaml`) — **ENABLED**, every 1h at :00 UTC, 30 min timeout
  - To add/remove a source: edit `config.yaml` `newsletterSources` and redeploy — no scheduler change needed.

## Multi-Agent Environment
Multiple AI agents work on this project. Check git status before starting, pull frequently, keep changes atomic.

## Collaboration
Ask before implementing unclear requirements. Propose approach before big changes. Flag risks explicitly.

## Maintaining This Document
Update when: new tool added → Tech Stack; new convention → Conventions; infra change → relevant section.

 ###Post-Implementation                                                                                   
  - After implementing a change, always run tests (`npm run test`, `uv run pytest`) and type checks (`npx   
  tsc --noEmit`) before considering it done.                                                                
  - For frontend UI changes, browser-test the actual behavior using Playwright.                             
  - If all tests and verification pass, commit the change automatically