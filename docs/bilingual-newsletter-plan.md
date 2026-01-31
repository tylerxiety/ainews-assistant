# Bilingual Newsletter Plan

**Overall Progress:** `100%`

## TLDR
Add full Chinese translation and audio support for newsletter content. New issues will be processed with both English and Chinese text/audio. Users see translated content and hear Chinese audio when UI is set to Chinese. Includes a one-time backfill endpoint for the latest existing issue.

## Critical Decisions

- **Translation model**: Use `gemini-3-flash-preview` (same as text cleaning) for English→Chinese translation
- **Schema approach**: Add `*_zh` columns to existing tables rather than separate language tables
- **Fallback behavior**: Skip segments with missing Chinese audio (no English fallback)
- **Backfill scope**: Manual endpoint for latest issue only, not a general reprocessing system

## Tasks

- [x] 🟩 **Step 1: Database schema migration**
  - [x] 🟩 Create migration `005_bilingual_content.sql`
  - [x] 🟩 Add `content_raw_zh`, `content_clean_zh`, `audio_url_zh`, `audio_duration_ms_zh` to `segments`
  - [x] 🟩 Add `label_zh` to `topic_groups`
  - [x] 🟩 Run migration on Supabase

- [x] 🟩 **Step 2: Backend translation service**
  - [x] 🟩 Add translation prompt to `config.yaml`
  - [x] 🟩 Add `_translate_texts_batch()` method in `processor.py`
  - [x] 🟩 Batch translate: content_raw → content_raw_zh, content_clean → content_clean_zh, label → label_zh

- [x] 🟩 **Step 3: Update processing pipeline for bilingual audio**
  - [x] 🟩 Modify `_generate_audio()` to accept language parameter
  - [x] 🟩 Update `process_newsletter()` to generate both EN and ZH audio per segment
  - [x] 🟩 Store `audio_url_zh` and `audio_duration_ms_zh` in database
  - [x] 🟩 Handle translation/TTS failures gracefully (leave `*_zh` columns null)

- [x] 🟩 **Step 4: Backfill endpoint for latest issue**
  - [x] 🟩 Add `/backfill-chinese` endpoint in `main.py`
  - [x] 🟩 Fetch latest issue and its segments from database
  - [x] 🟩 Translate existing English content to Chinese
  - [x] 🟩 Generate Chinese audio for all segments
  - [x] 🟩 Update database with Chinese content and audio URLs
  - [x] 🟩 add testing option for n segments

- [x] 🟩 **Step 5: Frontend TypeScript types**
  - [x] 🟩 Update `Segment` interface with `content_raw_zh`, `audio_url_zh`, `audio_duration_ms_zh`
  - [x] 🟩 Update `TopicGroup` interface with `label_zh`

- [x] 🟩 **Step 6: Frontend display logic**
  - [x] 🟩 Update `SegmentList.tsx` to display `content_raw_zh` when language is Chinese
  - [x] 🟩 Update `SidePanel.tsx` to display `label_zh` for topic headers when Chinese
  - [x] 🟩 Filter out segments with null `audio_url_zh` in Chinese mode

- [x] 🟩 **Step 7: Frontend audio playback**
  - [x] 🟩 Update `Player.tsx` to select `audio_url_zh` or `audio_url` based on language
  - [x] 🟩 Update duration calculations to use `audio_duration_ms_zh` when in Chinese mode
  - [x] 🟩 Handle language switch mid-playback (reload playlist with correct audio URLs)

## Testing (Required)

### Approach
browser testing via Playwright MCP

### Test Scenarios
- [x] 🟩 New issue processing generates both English and Chinese audio files in GCS
- [x] 🟩 Segments table contains populated `content_raw_zh`, `audio_url_zh` columns after processing
- [x] 🟩 test `/backfill-chinese` endpoint successfully adds Chinese content for first 5 segments of the latest issue
- [x] 🟩 UI displays Chinese text (`content_raw_zh`) when language is set to Chinese
- [x] 🟩 Player plays Chinese audio when language is Chinese
- [x] 🟩 Switching language mid-playback switches to correct audio
- [x] 🟩 Segments with null `audio_url_zh` are skipped in Chinese mode

### Acceptance Criteria
- [x] New Cloud Run job produces segments with both `audio_url` and `audio_url_zh` populated
- [x] Chinese audio uses `cmn-CN-Chirp3-HD-Aoede` voice
- [x] Topic group headers display in Chinese (`label_zh`) when UI language is Chinese
- [x] Total playlist duration recalculates correctly when switching languages
- [x] Backfill endpoint returns success and populates Chinese columns for latest issue
