# Claude Code Instructions

> **Shared instructions**: See `AGENTS.md` for project overview, stack, and conventions.

## Claude-Specific

### Backend
- **Virtual environment**: Uses `uv`. Always run backend Python commands with:
  ```bash
  cd backend && uv run <command>
  ```
  For example: `cd backend && uv run python main.py` or `cd backend && uv run pytest`
