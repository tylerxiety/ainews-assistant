# Bilingual Newsletter Plan

**Overall Progress:** `0%`

## TLDR
Add full Chinese translation and audio support for newsletter content. New issues will be processed with both English and Chinese text/audio. Users see translated content and hear Chinese audio when UI is set to Chinese. Includes a one-time backfill endpoint for the latest existing issue.

## Critical Decisions

- **Translation model**: Use `gemini-3-flash-preview` (same as text cleaning) for English→Chinese translation
- **Schema approach**: Add `*_zh` columns to existing tables rather than separate language tables
- **Fallback behavior**: Skip segments with missing Chinese audio (no English fallback)
- **Backfill scope**: Manual endpoint for latest issue only, not a general reprocessing system

## Tasks

- [ ] 🟥 **Step 1: Database schema migration**
  - [ ] 🟥 Create migration `005_bilingual_content.sql`
  - [ ] 🟥 Add `content_raw_zh`, `content_clean_zh`, `audio_url_zh`, `audio_duration_ms_zh` to `segments`
  - [ ] 🟥 Add `label_zh` to `topic_groups`
  - [ ] 🟥 Run migration on Supabase

- [ ] 🟥 **Step 2: Backend translation service**
  - [ ] 🟥 Add translation prompt to `config.yaml`
  - [ ] 🟥 Add `_translate_texts_batch()` method in `processor.py`
  - [ ] 🟥 Batch translate: content_raw → content_raw_zh, content_clean → content_clean_zh, label → label_zh

- [ ] 🟥 **Step 3: Update processing pipeline for bilingual audio**
  - [ ] 🟥 Modify `_generate_audio()` to accept language parameter
  - [ ] 🟥 Update `process_newsletter()` to generate both EN and ZH audio per segment
  - [ ] 🟥 Store `audio_url_zh` and `audio_duration_ms_zh` in database
  - [ ] 🟥 Handle translation/TTS failures gracefully (leave `*_zh` columns null)

- [ ] 🟥 **Step 4: Backfill endpoint for latest issue**
  - [ ] 🟥 Add `/backfill-chinese` endpoint in `main.py`
  - [ ] 🟥 Fetch latest issue and its segments from database
  - [ ] 🟥 Translate existing English content to Chinese
  - [ ] 🟥 Generate Chinese audio for all segments
  - [ ] 🟥 Update database with Chinese content and audio URLs

- [ ] 🟥 **Step 5: Frontend TypeScript types**
  - [ ] 🟥 Update `Segment` interface with `content_raw_zh`, `audio_url_zh`, `audio_duration_ms_zh`
  - [ ] 🟥 Update `TopicGroup` interface with `label_zh`

- [ ] 🟥 **Step 6: Frontend display logic**
  - [ ] 🟥 Update `IssueList.tsx` to display `content_raw_zh` when language is Chinese
  - [ ] 🟥 Update `SidePanel.tsx` to display `label_zh` for topic headers when Chinese
  - [ ] 🟥 Filter out segments with null `audio_url_zh` in Chinese mode

- [ ] 🟥 **Step 7: Frontend audio playback**
  - [ ] 🟥 Update `Player.tsx` to select `audio_url_zh` or `audio_url` based on language
  - [ ] 🟥 Update duration calculations to use `audio_duration_ms_zh` when in Chinese mode
  - [ ] 🟥 Handle language switch mid-playback (reload playlist with correct audio URLs)

## Testing (Required)

### Approach
Manual browser testing + API testing with curl for backfill endpoint

### Test Scenarios
- [ ] 🟥 New issue processing generates both English and Chinese audio files in GCS
- [ ] 🟥 Segments table contains populated `content_raw_zh`, `audio_url_zh` columns after processing
- [ ] 🟥 `/backfill-chinese` endpoint successfully adds Chinese content to latest issue
- [ ] 🟥 UI displays Chinese text (`content_raw_zh`) when language is set to Chinese
- [ ] 🟥 Player plays Chinese audio when language is Chinese
- [ ] 🟥 Switching language mid-playback switches to correct audio
- [ ] 🟥 Segments with null `audio_url_zh` are skipped in Chinese mode

### Acceptance Criteria
- [ ] New Cloud Run job produces segments with both `audio_url` and `audio_url_zh` populated
- [ ] Chinese audio uses `cmn-CN-Chirp3-HD-Aoede` voice
- [ ] Topic group headers display in Chinese (`label_zh`) when UI language is Chinese
- [ ] Total playlist duration recalculates correctly when switching languages
- [ ] Backfill endpoint returns success and populates Chinese columns for latest issue
