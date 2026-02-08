# Q&A Localization Fix Plan

**Overall Progress:** `100%`

## TLDR
Fix Q&A to use Chinese context and prompts when UI language is set to Chinese. Currently both Q&A paths (manual mic and voice mode) always fetch English content from the database, causing Q&A responses to be based on English text even when the UI is in Chinese.

## Critical Decisions
- **Use existing Chinese columns**: The database already has `content_clean_zh` and `content_raw_zh` columns (populated by backfill). No schema changes needed.
- **Pass language as query param for WebSocket**: Add `?language=zh` to the WebSocket URL since WebSocket doesn't support form data.
- **Fallback to English**: If Chinese columns are empty, fall back to English content (graceful degradation).

## Tasks

- [x] 🟩 **Step 1: Fix `/ask-audio` context fetch**
  - [x] 🟩 Modify `ask_with_audio()` in `processor.py` (line ~772-785) to select Chinese columns when `language="zh"`
  - [x] 🟩 Build context from `content_clean_zh`/`content_raw_zh` with fallback to English columns

- [x] 🟩 **Step 2: Fix voice mode WebSocket**
  - [x] 🟩 Add `language` query parameter to `/ws/voice/{issue_id}` endpoint in `main.py` (line ~96)
  - [x] 🟩 Update `_fetch_issue_context()` in `main.py` (line ~77) to accept language and select appropriate columns
  - [x] 🟩 Pass language to `VoiceSession` constructor
  - [x] 🟩 Store language in `VoiceSession` and use it in `build_system_prompt()`

- [x] 🟩 **Step 3: Update frontend to send language for voice mode**
  - [x] 🟩 Modify `useVoiceMode.ts` to include `language` query param when opening WebSocket

## Testing (Required)

### Approach
Manual testing with browser + backend logs to verify correct language flow.

### Test Scenarios
- [ ] 🟥 Scenario 1: Switch UI to Chinese → use manual mic Q&A → response should be in Chinese based on Chinese newsletter content
- [ ] 🟥 Scenario 2: Switch UI to Chinese → use voice mode → voice responses should be in Chinese
- [ ] 🟥 Scenario 3: Use Q&A on section without Chinese backfill → should gracefully fall back to English content
- [ ] 🟥 Scenario 4: Switch UI back to English → Q&A should work in English as before

### Acceptance Criteria
- [ ] Manual mic Q&A returns Chinese audio when UI is Chinese
- [ ] Voice mode responds in Chinese when UI is Chinese
- [ ] Backend logs show Chinese columns being queried when `language=zh`
- [ ] English Q&A remains unaffected
