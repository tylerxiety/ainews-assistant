# Project Instructions

## Overview
AI News Assistant - PWA that converts AINews newsletter into listenable audio with visual sync, voice Q&A, and tap-to-bookmark to ClickUp. Newsletters are auto-processed every 6 hours via Cloud Scheduler.

## Tech Stack
- **Frontend**: Vite + React + TypeScript + plain CSS (PWA on Vercel)
- **Backend**: Python + FastAPI (Cloud Run)
- **Database**: Supabase (Postgres)
- **Storage**: Google Cloud Storage (audio files)
- **TTS**: Google Cloud TTS (Chirp 3 HD Aoede)
- **AI**: Gemini 3 Pro Preview (text cleaning + Q&A transcription)
- **Task Integration**: ClickUp API
- **Config**: Centralized `config.yaml` (shared by frontend/backend)

## Key Decisions
- **Voice Q&A uses MediaRecorder + server-side Gemini** (not Web Speech API) — Web Speech API had garbled transcription on iOS Safari/Chrome
- **Per-segment audio playback** — One TTS call per segment (no group-audio fallback); topic groups are for UI/ordering only
- **Single audio element for newsletter + Q&A** — Reuses unlocked audio element to bypass iOS autoplay restrictions

## Conventions

### Backend
- **Package manager**: `uv`
- **Running commands**: Always use `uv run` from the backend directory:
  ```bash
  cd backend && uv run <command>
  ```
  Example: `cd backend && uv run python main.py`

### Python
- Use `logging` module, not `print`
- Type hints for function signatures

### React/TypeScript
- Functional components with hooks
- Strict typing (no `any`)
- Proper useEffect cleanup

### General
- Keep solutions simple — don't over-engineer
- No debug code or TODOs in commits
- **All config changes go in `/config.yaml`** — frontend imports via rollup-plugin-yaml, backend loads with PyYAML

### Testing & Debugging
- Do NOT create standalone test scripts for commits. Temporary one‑off scripts are OK for local debugging, but must be deleted before final changes (keep in /tests/tmp).
- To verify functionality works: use existing API endpoints, REPL, or `curl`
- For debugging: add temporary logging, then remove it — don't create new files
- If a proper test suite is needed, discuss with user first before setting up pytest/testing infrastructure
- Use ngrok to expose local dev for mobile testing

### Documentation
- Agent-created dev docs (plans, specs) go in `docs/` with **lowercase** names (e.g., `auth-plan.md`)
- UPPERCASE names (e.g., `SETUP.md`) are reserved for user-created docs

### Credentials & Infrastructure
- **GCP**: Uses Application Default Credentials (ADC) — no explicit keys needed
- **CLIs available**: `gcloud`, `supabase`, `vercel`, `gh` (GitHub)
- **Use CLIs** for infra tasks (deployments, migrations, config) instead of asking user to do it manually
- **Always ask permission** before running commands that create, modify, or delete resources
- Read-only commands (status, list, logs) are fine without asking

## Multi-Agent Environment

This project uses multiple AI coding agents (Claude Code, Antigravity, etc.). To avoid conflicts:
- Check git status before starting work
- Pull latest changes frequently
- Keep changes focused and atomic
- Coordinate on shared files when possible

## Collaboration

- Ask before implementing if requirements are unclear
- Propose approach before big changes
- Flag risks and tradeoffs explicitly
- Don't assume requirements — ask clarifying questions

## Maintaining This Document

When you make changes that affect how to work in this codebase, update this file:
- New tool/framework added → Update Tech Stack
- New convention established → Add to Conventions
- Infrastructure change → Update relevant section
