# Parallel Features Implementation Plan

**Overall Progress:** `50%`

## TLDR

Two features developed in parallel:
1. **Q&A/Interrupt (Feature A)** — Voice-activated Q&A during audio playback. Tap mic to enter listen mode, ask questions about current topic, get spoken answers.
2. **General Newsletter Support (Feature B)** — Paste any newsletter issue URL to process and listen. Inline input in IssueList.

## Critical Decisions

- **Q&A trigger:** Tap-to-listen mode (not always-on or wake word) — simpler, no permission issues
- **Q&A context:** Current topic group only — no Twitter link content for MVP
- **Newsletter input:** Issue URL only (not RSS/homepage) — clear contract, avoids subscription model complexity
- **Newsletter UI:** Inline in IssueList (not separate page) — minimal, single screen
- **Parallel boundaries:** Feature A owns Player.tsx + `/ask` endpoint; Feature B owns IssueList.tsx + parser improvements

---

# Feature A: Q&A/Interrupt

**Owner:** Main development thread

## Tasks

- [x] 🟩 **Step 1: Backend `/ask` endpoint**
  - [x] 🟩 Add `ask()` method to `processor.py` — accepts question + topic context, calls Gemini, returns text response
  - [x] 🟩 Add `POST /ask` endpoint to `main.py` — params: `issue_id`, `group_id`, `question`
  - [x] 🟩 Generate TTS for response, upload to GCS, return audio URL + transcript

- [x] 🟩 **Step 2: Frontend STT integration**
  - [x] 🟩 Add Web Speech API hook (`useSpeechRecognition`) — handles start/stop, returns transcript
  - [x] 🟩 Add mic button to Player.tsx — toggles listen mode
  - [x] 🟩 Auto-pause newsletter audio when STT starts
  - [x] 🟩 Detect end of speech (silence or "done") — stop STT, send question

- [x] 🟩 **Step 3: Conversation UI in Player**
  - [x] 🟩 Add conversation state to Player.tsx — `messages: {role, text, audioUrl}[]`
  - [x] 🟩 Add collapsible conversation panel below controls — shows Q&A history
  - [x] 🟩 Add second `<audio>` element for response playback (separate from newsletter audio)

- [x] 🟩 **Step 4: Response playback flow**
  - [x] 🟩 On question submit: show loading state, call `/ask`, receive response
  - [x] 🟩 Play response audio, display transcript in conversation panel
  - [x] 🟩 On response end: auto-resume newsletter audio (if was playing before)

- [x] 🟩 **Step 5: Polish & edge cases**
  - [x] 🟩 Handle STT errors (no permission, not supported) — show fallback text input
  - [x] 🟩 Handle `/ask` errors — display error in conversation panel
  - [x] 🟩 Prevent overlapping requests (disable mic while processing)

---

# Feature B: General Newsletter Support

**Owner:** Background development thread

## Tasks

- [x] 🟩 **Step 1: URL input UI**
  - [x] 🟩 Add URL input form to top of IssueList.tsx — text field + submit button
  - [x] 🟩 Basic validation — must be valid URL, show inline error if not
  - [x] 🟩 Submit calls `POST /process?url=...`

- [x] 🟩 **Step 2: Processing status**
  - [x] 🟩 Add `processingStatus` state — `idle | processing | done | error`
  - [x] 🟩 Show inline progress indicator while processing ("Processing newsletter...")
  - [x] 🟩 On success: add new issue to list, auto-navigate to Player
  - [x] 🟩 On error: show error message, allow retry

- [x] 🟩 **Step 3: Parser improvements**
  - [x] 🟩 Test `_parse_newsletter()` against Substack HTML — adjust selectors if needed
  - [x] 🟩 Test against Buttondown HTML — adjust selectors if needed
  - [x] 🟩 Add fallback: if no structured content found, treat entire `<article>` or `<main>` as single segment

- [x] 🟩 **Step 4: Edge cases**
  - [x] 🟩 Handle duplicate URL submission — check if issue already exists, navigate to existing
  - [x] 🟩 Handle unreachable URLs — return clear error message
  - [x] 🟩 Handle empty/unparseable content — return error with guidance

---

## File Ownership (Parallel Safety)

| File | Feature A | Feature B |
|------|-----------|-----------|
| `frontend/src/components/Player.tsx` | ✅ Owns | ❌ No touch |
| `frontend/src/components/IssueList.tsx` | ❌ No touch | ✅ Owns |
| `backend/main.py` | ✅ Add `/ask` | ❌ No touch (existing `/process` works) |
| `backend/processor.py` | ✅ Add `ask()` method | ✅ Modify `_parse_newsletter()` only |
| `frontend/src/types.ts` | ✅ Add conversation types | ✅ Add processing status types |

**Rule:** If both features need to touch the same file, coordinate before editing.

---

## Not in Scope (Fast-follow)

- Wake word detection for Q&A
- Twitter link content in Q&A context
- RSS/homepage URL detection
- Newsletter subscription management
- Dedicated import page with progress bar
