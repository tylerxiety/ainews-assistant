---
name: source-command-create-plan
description: Plan Creation Stage
---

# Plan Creation Stage

Based on our full exchange, produce a markdown plan document.

Requirements for the plan:

- Include clear, minimal, concise steps.
- Track the status of each step using these emojis:
  - 🟩 Done
  - 🟨 In Progress
  - 🟥 To Do
- Include dynamic tracking of overall progress percentage (at top).
- Do NOT add extra scope or unnecessary complexity beyond explicitly clarified details.
- Steps should be modular, elegant, minimal, and integrate seamlessly within the existing codebase.

Markdown Template:

# Feature Implementation Plan

**Overall Progress:** `0%`

## TLDR
Short summary of what we're building and why.

## Critical Decisions
Key architectural/implementation choices made during exploration:
- Decision 1: [choice] - [brief rationale]
- Decision 2: [choice] - [brief rationale]

## Tasks:

- [ ] 🟥 **Step 1: [Name]**
  - [ ] 🟥 Subtask 1
  - [ ] 🟥 Subtask 2

- [ ] 🟥 **Step 2: [Name]**
  - [ ] 🟥 Subtask 1
  - [ ] 🟥 Subtask 2

...

## Testing (Required)

### Approach
[browser agent or MCP tools / API (curl/REPL) / unit tests / manual]

### Test Scenarios
- [ ] 🟥 Scenario 1: [user action or input] → [expected outcome]
- [ ] 🟥 Scenario 2: [edge case] → [expected behavior]
- [ ] 🟥 Scenario 3: [error case] → [expected handling]

### Acceptance Criteria
- [ ] [Observable proof that the feature works end-to-end]
- [ ] [Key behavior verified]

**Note:** Be specific. "Works correctly" is not a criterion. "Audio resumes from saved position after Q&A ends" is.

## Output Location

Save the plan to `docs/no-<feature-name>-plan.md` (lowercase, hyphenated). UPPERCASE names are reserved for user-created docs.

It's not time to build yet. Just write the clear plan document. No extra complexity or extra scope beyond what we discussed.
