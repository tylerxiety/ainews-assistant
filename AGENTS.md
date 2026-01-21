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

### Python
- Use `logging` module, not `print`
- DataFrames: `df_xxx` naming (e.g., `df_results`, `df_eval`)
- Type hints for function signatures

### React/TypeScript
- Functional components with hooks
- Strict typing (no `any`)
- Proper useEffect cleanup

### General
- Keep solutions simple — don't over-engineer
- No debug code or TODOs in commits

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
