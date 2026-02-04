# Project Instructions

## Overview
AI News Assistant - PWA that converts AINews newsletter into listenable audio with visual sync, voice commands/Q&A, bilingual support (EN/ZH), and tap-to-bookmark to ClickUp. Auto-processed every 6 hours via Cloud Scheduler.

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
- **Fallback Q&A**: MediaRecorder + server-side Gemini when voice mode is off
- **Per-segment audio**: One TTS call per segment; topic groups are for UI/ordering only
- **Single `<audio>` element**: Newsletter playback only; Q&A audio plays via AudioContext
- **UI Architecture**: `Player.tsx` orchestrates state; `SegmentList` (content), `AudioBar` (controls), `SidePanel` (TOC + Q&A)
- **Bilingual content**: Separate `*_zh` columns in DB; skip segments without Chinese audio when UI is ZH
- **UI localization**: Simple JSON locale files with React context; persisted to localStorage; both EN/ZH voice commands always recognized

## Conventions

### Backend
- **Package manager**: `uv` — always run `cd backend && uv run <command>`
- Use `logging` module (not `print`), type hints for function signatures

### Frontend
- Functional components with hooks, strict typing (no `any`), proper useEffect cleanup
- Two-color palette (black + orange), lucide-react icons

### General
- Keep solutions simple — don't over-engineer
- No debug code or TODOs in commits
- **All config in `/config.yaml`** — frontend imports via rollup-plugin-yaml, backend via PyYAML

### Testing
- Test against ngrok URL: https://vicarly-subtransparent-reese.ngrok-free.dev, NOT dev server:
  ```bash
  cd frontend && VITE_API_URL="" npm run build
  cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8080
  ngrok http 8080
  ```
- No standalone test scripts in commits; temp scripts in `tests/tmp/` (delete before commit)

### Documentation
- Agent docs in `docs/` with numbered prefix, lowercase (e.g., `13-auth-plan.md`)
- UPPERCASE names reserved for user-created docs

### Infrastructure
- GCP uses ADC — no explicit keys needed
- CLIs available: `gcloud`, `supabase`, `vercel`, `gh`
- Ask permission before create/modify/delete commands; read-only commands are fine

## Multi-Agent Environment
Multiple AI agents work on this project. Check git status before starting, pull frequently, keep changes atomic.

## Collaboration
Ask before implementing unclear requirements. Propose approach before big changes. Flag risks explicitly.

## Maintaining This Document
Update when: new tool added → Tech Stack; new convention → Conventions; infra change → relevant section.
