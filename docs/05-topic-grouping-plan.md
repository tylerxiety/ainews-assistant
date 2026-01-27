# Topic Grouping & Batch Audio Plan

**Overall Progress:** `100%`

## TLDR

Restructure segments into topic groups that match the newsletter layout. Each topic group (title + bullet items) gets ONE combined audio file, reducing API calls by ~75%. Bookmarks target individual bullet items by ID/position (text-based), not audio timestamps.

## Critical Decisions

- **UI layout**: One box per topic group containing title + bullet items (matches newsletter format)
- **Audio strategy**: Combined audio per topic group with pause markers between items (listener still perceives segmentation)
- **Bookmark tracking**: Text/position-based (item ID within group), not audio timestamp-based
- **Q&A scope**: Future Q&A will use bullet item as context scope (simpler than timestamp mapping)

## Tasks

- [x] ✅ **Step 1: Fix missing topic titles in parser**
  - [x] ✅ Update `_parse_newsletter()` to detect `<p><strong>...</strong></p>` as `topic_header` type
  - [x] ✅ Ensure topic headers are captured before their associated `<li>` items

- [x] ✅ **Step 2: Add topic grouping schema**
  - [x] ✅ Create migration: add `topic_group_id` column to `segments` table
  - [x] ✅ Add `topic_groups` table with `id`, `issue_id`, `audio_url`, `audio_duration_ms`, `order_index`
  - [x] ✅ Update bookmarks to reference `segment_id` (items within groups, unchanged)

- [x] ✅ **Step 3: Update parser to group segments by topic**
  - [x] ✅ Group `topic_header` + following `item` segments into topic groups
  - [x] ✅ Assign `topic_group_id` to each segment within a group

- [x] ✅ **Step 4: Implement batch Gemini text cleaning**
  - [x] ✅ Create `_clean_texts_batch()` method that accepts list of texts
  - [x] ✅ Return list of cleaned texts in same order
  - [x] ✅ Update processing to batch clean all texts in a topic group (1 API call)

- [x] ✅ **Step 5: Implement combined audio generation**
  - [x] ✅ Concatenate cleaned texts with pause markers (e.g., "... ... ..." or SSML `<break>`)
  - [x] ✅ Generate single audio file per topic group
  - [x] ✅ Store `audio_url` and `audio_duration_ms` on `topic_groups` table

- [x] ✅ **Step 6: Update frontend UI to display topic groups**
  - [x] ✅ Fetch topic groups with their segments
  - [x] ✅ Render each topic group as one box: title + bullet items
  - [x] ✅ Single audio player per topic group
  - [x] ✅ Bookmark button on each bullet item (existing logic, unchanged target)

- [x] ✅ **Step 7: Update playback logic**
  - [x] ✅ Play combined audio for topic group
  - [x] ✅ Highlight current topic group during playback
  - [x] ✅ Auto-advance to next topic group when audio ends

## Output Location

`docs/topic-grouping-plan.md`
