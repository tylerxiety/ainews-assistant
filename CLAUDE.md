# Claude Code Instructions

> **Shared instructions**: See `AGENTS.md` for project overview, stack, and conventions.

## Claude-Specific

### Cost Optimization (Opus only)

When running as Opus on heavy exploration/review tasks, use a two-phase approach:

1. **Phase 1**: Spawn a Sonnet subagent (`Task` tool with `model="sonnet"`) for:
   - Codebase scanning and file reading
   - Web searches for external docs
   - Initial categorization of findings

2. **Phase 2**: Opus synthesizes the subagent's summary and does:
   - Detailed analysis and reasoning
   - Integration insights
   - Clarifying questions for user

**Applies to skills**: `/explore`, `/review`, `/peer-review`, `/document`

**Does NOT apply when**:
- Already running as Sonnet or Haiku (no benefit)
- Implementation tasks (`/execute`, `/verify`) - need direct file access to write code
- Quick tasks (`/create-issue`) - subagent overhead exceeds benefit
