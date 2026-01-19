# Newsletter Audio Player — Project Brief

## What We're Building

A PWA that converts the [AINews newsletter](https://news.smol.ai/) into a listenable audio experience with clean TTS (no "@mentions", "/r/", or raw URLs read aloud), visual sync (auto-scroll + highlight current item), and tap-to-bookmark items to ClickUp.

**Target user:** The developer building this (personal tool, single user for MVP).

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | Vite + React + plain CSS | PWA-enabled, deployed on Vercel |
| Backend | Python (Cloud Run) | Processes newsletters, generates audio |
| Database | Supabase (Postgres) | Stores issues, segments, bookmarks |
| Audio Storage | Google Cloud Storage | Stores generated audio files |
| TTS | Google Cloud TTS (Chirp 3 HD Aoede) | Female voice, `en-US-Chirp3-HD-Aoede` |
| Text Cleaning | Gemini 3 Pro | Cleans newsletter text for natural speech |
| Task Integration | ClickUp API | Bookmark items as tasks |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GCP (Cloud Run + Storage)                   │
│                                                                 │
│  Cloud Scheduler ──▶ Processor Service ──▶ Cloud Storage        │
│  (every 6 hours)     │                     (audio files)        │
│                      ├─ Fetch RSS                               │
│                      ├─ Parse HTML into items                   │
│                      ├─ Clean text via Gemini 3 Pro             │
│                      ├─ Generate TTS per item                   │
│                      └─ Store metadata in Supabase              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Vercel (Frontend PWA)                       │
│                                                                 │
│  React App                                                      │
│  ├─ Issue list view                                             │
│  ├─ Player view                                                 │
│  │   ├─ Renders newsletter HTML                                 │
│  │   ├─ Audio player (controls, speed)                          │
│  │   ├─ Auto-scroll + highlight synced to audio                 │
│  │   └─ Tap item → bookmark to ClickUp                          │
│  └─ Settings (ClickUp list ID, voice preference)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model (Supabase)

```sql
-- Newsletter issues
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  published_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual items (per-item audio for fine-grained sync)
CREATE TABLE segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
  segment_type TEXT NOT NULL, -- 'section_header' | 'item'
  content_raw TEXT NOT NULL,  -- Original text with links
  content_clean TEXT NOT NULL, -- Cleaned for TTS
  links JSONB DEFAULT '[]',   -- [{text, url}] for tap-to-open
  audio_url TEXT,             -- GCS URL
  audio_duration_ms INTEGER,
  order_index INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookmarks saved to ClickUp
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_id UUID REFERENCES segments(id) ON DELETE CASCADE,
  clickup_task_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_segments_issue_id ON segments(issue_id);
CREATE INDEX idx_segments_order ON segments(issue_id, order_index);
```

---

## Key Implementation Details

### Text Cleaning Rules (Gemini prompt)

| Pattern | Transformation |
|---------|----------------|
| `@username` | "[username] tweeted" |
| `/r/subreddit` | "the [subreddit] subreddit" |
| `[link text](url)` | Just read "link text", skip URL |
| Section headers | Prefix with "Now:" e.g., "Now: AI Twitter Recap" |

### Audio Sync Strategy

- Each segment has `audio_duration_ms`
- Frontend calculates cumulative start time per segment
- On `timeupdate` event, find current segment, scroll into view + highlight
- Concatenate audio files client-side OR use single playlist

### ClickUp Integration

- Personal API token (user provides in settings)
- POST to `/api/v2/list/{list_id}/task`
- Payload: `{ name: segment.content_raw.slice(0, 100), description: links[0]?.url }`

---

## Environment Variables

### Frontend (.env.local)
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_CLICKUP_LIST_ID=
```

### Backend (Cloud Run)
```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
GCP_PROJECT_ID=
GCP_REGION=
GCS_BUCKET_NAME=

```

---

## Scaffold Instructions

### Step 1: Create monorepo structure

```
newsletter-player/
├── frontend/          # Vite + React PWA
├── backend/           # Python Cloud Run service
├── supabase/          # Migrations
│   └── migrations/
├── docs/              # Documentation
└── README.md
```

### Step 2: Frontend scaffold

```bash
cd newsletter-player
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install @supabase/supabase-js
```

Create PWA manifest and service worker config (use vite-plugin-pwa).

### Step 3: Backend scaffold

```bash
cd newsletter-player/backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn google-cloud-texttospeech google-cloud-storage google-cloud-aiplatform supabase httpx beautifulsoup4 feedparser
```

Create:
- `main.py` — FastAPI app with `/process` endpoint
- `processor.py` — RSS fetch, parse, clean, TTS logic
- `Dockerfile` — For Cloud Run deployment
- `requirements.txt`

### Step 4: Supabase migration

```bash
cd newsletter-player
npx supabase init
# Copy the SQL from Data Model section into supabase/migrations/001_initial.sql
npx supabase db push
```

---

## First Milestone: End-to-End Smoke Test

**Goal:** Process one newsletter issue, play audio in browser.

1. Backend: Manually trigger `/process?url=https://news.smol.ai/issues/26-01-16-chatgpt-ads/`
2. Verify: Segments appear in Supabase, audio files in GCS
3. Frontend: List issues, click one, hear audio play

No sync, no bookmarks, no polish — just prove the pipeline works.

---

## Out of Scope (MVP)

- User auth
- Multiple newsletters
- Offline/download
- Voice commands
- Interrupt-to-ask
- Multi-user / productization
