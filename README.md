# AI News Assistant

A PWA that converts the [AINews](https://buttondown.com/ainews) newsletter into listenable audio with visual sync, voice commands/Q&A, bilingual support (EN/ZH), and tap-to-bookmark to ClickUp. Auto-processed every 6 hours via Cloud Scheduler.

## Tech Stack

- **Frontend**: Vite + React 19 + TypeScript (PWA, deployed on Vercel)
- **Backend**: Python + FastAPI (Cloud Run)
- **Database**: Supabase (Postgres)
- **Storage**: Google Cloud Storage (audio files)
- **TTS**: Google Cloud TTS
- **AI**: Gemini (text cleaning, Q&A, voice mode)

## Setup

### Backend

```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

## Usage

- **Listen**: Pick a newsletter issue, tap a segment or press play. Segments auto-advance.
- **Playback controls**: Play/pause, progress bar seek, and speed toggle (1x/1.25x/1.5x/2x).
- **Navigate**: Use the table of contents (list icon) to jump between sections, or tap any segment directly.
- **Voice mode**: Tap the waveform button to go hands-free. Say commands like *play*, *pause*, *next*, *previous*, *bookmark*, *rewind*, or *forward*. Ask questions about the content and get spoken answers.
- **Bookmark**: Tap the pin icon on a segment to save it as a ClickUp task. Configure your ClickUp API token and list ID in Settings.

