# Claude Code Instructions

### Context Loading
You MUST read `AGENTS.md` at the start of any new task or session to load the project's shared instructions and conventions.

### Debugging
When I report a bug, don't start by trying to fix it. Instead, start by writing a test that reproduces the bug. Then, have subagents try to fix the bug and prove it with a passing test.

### Cost Optimization (Opus only)
When running as Opus on heavy exploration/review tasks, use a two-phase approach:

1. Phase 1: Spawn a Sonnet subagent (`Task` tool with `model="sonnet"`) for:
   - Codebase scanning and file reading
   - Web searches for external docs
   - Initial categorization of findings

2. Phase 2: Opus synthesizes the subagent's summary and does:
   - Detailed analysis and reasoning
   - Integration insights
   - Clarifying questions for user

Applies to skills: `/explore`, `/review`, `/peer-review`, `/document`

Does NOT apply when:
- Already running as Sonnet or Haiku (no benefit)
- Implementation tasks (`/execute`, `/verify`) - need direct file access to write code
- Quick tasks (`/create-issue`) - subagent overhead exceeds benefit