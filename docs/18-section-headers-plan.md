# Section Headers Implementation Plan

**Overall Progress:** `85%`

## TLDR
Preserve section headers (e.g., "AI Twitter Recap", "AI Reddit Recap") in the newsletter output. Currently, section headers are parsed but filtered out because they have no item segments. Fix: keep them as topic groups with `is_section_header=true`, render them as visual dividers in the TOC and larger headings in the content area, and generate audio ("Now: AI Twitter Recap").

## Critical Decisions
- **Data model**: Add `is_section_header BOOLEAN DEFAULT FALSE` to `topic_groups` table (simplest approach, no schema complexity)
- **Audio handling**: Section headers get audio like topic headers—the cleaned label is spoken as "Now: AI Twitter Recap" (via existing text-cleaning prompt)
- **TOC display**: Flat list with section headers styled as dividers (not collapsible/expandable)
- **Backfill**: Re-process existing newsletters to add section headers

## Tasks

- [x] 🟩 **Step 1: Database Migration**
  - [x] 🟩 Create `006_section_headers.sql`: Add `is_section_header BOOLEAN DEFAULT FALSE` to `topic_groups`
  - [ ] 🟥 Apply migration to Supabase (requires manual run)

- [x] 🟩 **Step 2: Backend - Preserve Section Headers**
  - [x] 🟩 Update `_group_segments()` (`processor.py:499-547`): Track `segment_type` in group dict, don't filter out section headers
  - [x] 🟩 Update DB insert payload (`processor.py:291-302`): Include `is_section_header` field based on tracked segment type
  - [x] 🟩 Handle section header audio: Section headers have no items, so generate standalone audio for the label only

- [x] 🟩 **Step 3: Frontend - Types & Data Fetching**
  - [x] 🟩 Update `TopicGroup` interface (`types.ts:33-45`): Add `is_section_header?: boolean`
  - [x] 🟩 Verify `fetchIssueWithGroups` (`supabase.ts`) returns the new field (works automatically)

- [x] 🟩 **Step 4: Frontend - Render Section Headers**
  - [x] 🟩 Update `SegmentList.tsx`: Render section headers as `<h2>` with distinct styling, topic headers as `<h3>` (current behavior)
  - [x] 🟩 Add CSS for section header styling (larger font, border/spacing to separate sections)

- [x] 🟩 **Step 5: Frontend - TOC with Dividers**
  - [x] 🟩 Update `SidePanel.tsx` TOC: Style section headers as dividers (clickable, styled differently)

- [x] 🟩 **Step 6: Backfill Existing Newsletters**
  - [x] 🟩 Create backfill endpoint `/backfill-section-headers` in `main.py`
  - [ ] 🟥 Run backfill on production data (requires manual run after migration)

## Testing (Required)

### Approach
Manual testing via browser + API (curl) to verify end-to-end flow.

### Test Scenarios
- [ ] 🟥 Process new newsletter → section headers appear in DB with `is_section_header=true`
- [ ] 🟥 Section header audio plays "Now: AI Twitter Recap" before first topic in that section
- [ ] 🟥 UI renders section headers as larger `<h2>` headings between topic groups
- [ ] 🟥 TOC shows section headers as visual dividers between topics
- [ ] 🟥 Backfill existing newsletter → section headers added correctly

### Acceptance Criteria
- [ ] "AI Twitter Recap", "AI Reddit Recap", etc. appear as distinct section headings in the newsletter UI
- [ ] Section headers have audio that speaks the section name
- [ ] TOC displays section headers as dividers separating topic entries
- [ ] Existing newsletters show section headers after backfill
