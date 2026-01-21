# Project Instructions

## Overview
AI News Assistant - PWA that converts AINews newsletter into listenable audio with visual sync and tap-to-bookmark to ClickUp.

## Tech Stack
- **Frontend**: Vite + React + TypeScript + plain CSS (PWA on Vercel)
- **Backend**: Python + FastAPI (Cloud Run)
- **Database**: Supabase (Postgres)
- **Storage**: Google Cloud Storage (audio files)
- **TTS**: Google Cloud TTS (Chirp 3 HD Aoede)
- **Text Cleaning**: Gemini 3 Pro
- **Task Integration**: ClickUp API

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

### Testing & Debugging
- **Do NOT create standalone test scripts** (e.g., `test_*.py`, `simple_test.py`, `check_*.py`)
- To verify functionality works: use existing API endpoints, REPL, or `curl`
- For debugging: add temporary logging, then remove it — don't create new files
- If a proper test suite is needed, discuss with user first before setting up pytest/testing infrastructure

### Documentation
- Agent-created dev docs (plans, specs) go in `docs/` with **lowercase** names (e.g., `auth-plan.md`)
- UPPERCASE names (e.g., `SETUP.md`) are reserved for user-created docs

### Credentials & Infrastructure
- **GCP**: Uses Application Default Credentials (ADC) — no explicit keys needed
- **CLIs available**: `gcloud`, `supabase`, `vercel`, `gh` (GitHub)
- **Use CLIs** for infra tasks (deployments, migrations, config) instead of asking user to do it manually
- **Always ask permission** before running commands that create, modify, or delete resources
- Read-only commands (status, list, logs) are fine without asking

## Collaboration

- Ask before implementing if requirements are unclear
- Propose approach before big changes
- Flag risks and tradeoffs explicitly
- Don't assume requirements — ask clarifying questions
