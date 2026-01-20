# Newsletter Audio Player


A PWA that converts the [AINews newsletter](https://news.smol.ai/) into a listenable audio experience with clean TTS, visual sync, and ClickUp integration.

## 🚀 Live Demo

| Service | URL |
|---------|-----|
| **Frontend PWA** | [https://ainews-assistant.vercel.app](https://ainews-assistant.vercel.app) |
| **Backend API** | [https://newsletter-processor-872179428244.us-central1.run.app/docs](https://newsletter-processor-872179428244.us-central1.run.app/docs) |


## Architecture

- **Frontend**: Vite + React PWA (deployed on Vercel)
- **Backend**: Python FastAPI on Google Cloud Run
- **Database**: Supabase (Postgres)
- **Storage**: Google Cloud Storage (audio files)
- **TTS**: Google Cloud TTS (Chirp 3 HD Aoede)
- **Text Cleaning**: Gemini 1.5 Pro

## Project Structure

```
ainews-assistant/
├── frontend/          # React PWA
│   ├── src/
│   ├── public/
│   ├── .env.example
│   └── package.json
├── backend/           # Python FastAPI service
│   ├── main.py
│   ├── processor.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── supabase/          # Database migrations
│   └── migrations/
│       └── 001_initial_schema.sql
├── docs/              # Documentation
└── PROJECT_BRIEF.md   # Detailed project specification
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Google Cloud Platform account
- Supabase account
- ClickUp account (for bookmarking)

### 1. Database Setup (Supabase)

1. Create a new Supabase project at https://supabase.com
2. Run the migration:
   ```bash
   cd supabase
   npx supabase db push
   ```
3. Get your Supabase URL and keys from the project settings

### 2. Backend Setup

1. Set up Google Cloud Project:
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id

   # Enable required APIs
   gcloud services enable texttospeech.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable run.googleapis.com
   ```

2. Create a GCS bucket:
   ```bash
   gsutil mb -l us-central1 gs://your-bucket-name
   ```

3. Configure backend environment:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. Install dependencies:
   ```bash
   uv sync
   ```

5. Run locally:
   ```bash
   uv run uvicorn main:app --reload
   ```

6. Deploy to Cloud Run:
   ```bash
   gcloud run deploy newsletter-processor \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars SUPABASE_URL=xxx,SUPABASE_SERVICE_KEY=xxx,...
   ```

### 3. Frontend Setup

1. Configure environment:
   ```bash
   cd frontend
   cp .env.example .env.local
   # Edit .env.local with your Supabase credentials
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run development server:
   ```bash
   npm run dev
   ```

4. Deploy to Vercel:
   ```bash
   npm install -g vercel
   vercel
   ```

## First Milestone: End-to-End Test

Test the complete pipeline:

1. **Process a newsletter** (backend):
   ```bash
   curl -X POST http://localhost:8080/process \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"}'
   ```

2. **Verify in Supabase**:
   - Check `issues` table for the new entry
   - Check `segments` table for parsed items
   - Verify `audio_url` fields are populated

3. **Test in browser**:
   - Open frontend (http://localhost:5173)
   - Navigate to issue list
   - Click on the processed issue
   - Verify audio playback works

## Development Workflow

### Backend Development

```bash
cd backend
uv run uvicorn main:app --reload --port 8080
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Database Changes

```bash
cd supabase
# Create new migration
npx supabase migration new migration_name

# Apply migrations
npx supabase db push
```

## Environment Variables

### Frontend (.env.local)
- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Supabase anonymous key
- `VITE_CLICKUP_LIST_ID`: ClickUp list ID for bookmarks

### Backend (.env)
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `GCP_PROJECT_ID`: Google Cloud project ID
- `GCP_REGION`: GCP region (e.g., us-central1)
- `GCS_BUCKET_NAME`: Cloud Storage bucket name
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON (optional)

## Tech Stack Details

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend Framework | React + Vite | Fast dev experience, PWA support |
| UI | Plain CSS | Lightweight, no framework overhead |
| State Management | React hooks | Simple, built-in |
| Backend Framework | FastAPI | Async Python, auto docs |
| TTS | Google Cloud TTS | High-quality Chirp 3 HD voice |
| Text Processing | Gemini 1.5 Pro | Clean text for natural speech |
| Database | Supabase | Postgres with real-time subscriptions |
| Storage | GCS | Audio file hosting |
| Deployment | Vercel + Cloud Run | Serverless, auto-scaling |

## Features Roadmap

### MVP (Current)
- [x] Scaffold monorepo structure
- [x] RSS feed parsing
- [x] Text cleaning with Gemini
- [x] Audio generation with TTS
- [x] Basic audio player UI
- [x] Issue list view

### Phase 2
- [x] Audio sync with visual highlighting
- [x] Auto-scroll during playback
- [x] ClickUp bookmark integration
- [x] Playback speed control
- [x] PWA offline support

### Future
- [ ] Cloud Scheduler automation (every 6 hours)
- [ ] Voice preference settings
- [ ] Download episodes
- [ ] Background audio
- [ ] Skip forward/backward

## Contributing

This is a personal project for MVP. Contributions welcome after initial release.

## License

MIT
