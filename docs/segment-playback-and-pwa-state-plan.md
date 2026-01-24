# Segment Playback & PWA State Persistence Plan

**Overall Progress:** `0%`

## TLDR

Two UI improvements:
1. **Per-segment playback:** Users can tap individual segments to play them (not just whole topics). Requires switching from combined group audio to per-segment audio files.
2. **PWA state persistence:** When iOS PWA is backgrounded and returns, the app restores the user's position (highlights and scrolls to the last segment) instead of resetting to home.

## Critical Decisions

- **Per-segment audio files:** Generate one TTS call per segment instead of combining. Gap between segments is acceptable (mimics reading).
- **localStorage-only for state:** No URL changes. Store `{ issueId, groupIndex, segmentIndex, isPlaying, savedAt }`.
- **Resume granularity:** Segment start only (no mid-segment resume).
- **New newsletters only:** No migration of existing data; changes apply to newly processed issues.
- **Expiration:** 24 hours, configurable in `config.yaml`.

## Tasks

### Backend Changes

- [ ] 🟥 **Step 1: Database schema update**
  - [ ] 🟥 Add `audio_url` (text, nullable) to `segments` table
  - [ ] 🟥 Add `audio_duration_ms` (integer, nullable) to `segments` table

- [ ] 🟥 **Step 2: Update processor for per-segment audio**
  - [ ] 🟥 Modify `_generate_audio` to accept segment ID for unique blob naming
  - [ ] 🟥 Update `process_group` to generate audio per segment (not combined)
  - [ ] 🟥 Store `audio_url` and `audio_duration_ms` on each segment
  - [ ] 🟥 Remove group-level audio generation (keep `audio_url` on group as null for backward compat)

### Frontend Changes

- [ ] 🟥 **Step 3: Update types and data fetching**
  - [ ] 🟥 Add `audio_url` and `audio_duration_ms` to `Segment` type
  - [ ] 🟥 Ensure `fetchIssueWithGroups` returns segment audio fields

- [ ] 🟥 **Step 4: Per-segment playback in Player**
  - [ ] 🟥 Add `currentSegmentIndex` state alongside `currentGroupIndex`
  - [ ] 🟥 Add `handleSegmentClick(groupIndex, segmentIndex)` handler
  - [ ] 🟥 Update audio source logic to use `segment.audio_url`
  - [ ] 🟥 On audio end: advance to next segment, or next group if last segment
  - [ ] 🟥 Highlight current segment (CSS class `active` on segment)
  - [ ] 🟥 Auto-scroll to current segment (not just group)

- [ ] 🟥 **Step 5: PWA state persistence**
  - [ ] 🟥 Add `playbackStateExpiration` to `config.yaml` (default: 24 hours in ms)
  - [ ] 🟥 Create `usePlaybackState` hook or inline logic:
    - [ ] 🟥 Save state to localStorage on `visibilitychange` (hidden) and `beforeunload`
    - [ ] 🟥 Save: `{ issueId, groupIndex, segmentIndex, isPlaying, savedAt }`
  - [ ] 🟥 On Player mount: restore state if valid (same issueId, not expired)
  - [ ] 🟥 On restore: set `currentGroupIndex`, `currentSegmentIndex`, scroll to segment, highlight
  - [ ] 🟥 Clear saved state when newsletter finishes or user navigates away

- [ ] 🟥 **Step 6: Differentiate tap vs scroll on segments**
  - [ ] 🟥 Track pointer position on `pointerdown`
  - [ ] 🟥 On `pointerup`, only trigger playback if movement < threshold (e.g., 10px)
  - [ ] 🟥 Ensure links and bookmark buttons still work via `stopPropagation`

### Config Changes

- [ ] 🟥 **Step 7: Add config entries**
  - [ ] 🟥 Add `playback_state_expiration_ms: 86400000` to `config.yaml` (frontend section)
  - [ ] 🟥 Expose in frontend `CONFIG` object

## Testing (Required)

### Approach
Browser-based manual testing on iOS PWA and desktop Chrome.

### Test Scenarios

- [ ] 🟥 **Scenario 1:** Tap segment in current group → audio plays from that segment's start
- [ ] 🟥 **Scenario 2:** Tap segment in different group → switches group, plays that segment
- [ ] 🟥 **Scenario 3:** Segment ends → next segment in group auto-plays
- [ ] 🟥 **Scenario 4:** Last segment in group ends → first segment of next group auto-plays
- [ ] 🟥 **Scenario 5:** Last segment of last group ends → playback stops, no crash
- [ ] 🟥 **Scenario 6:** Scroll through segments without triggering playback
- [ ] 🟥 **Scenario 7:** iOS PWA: playing audio, background app, return → audio continues, correct segment highlighted and visible
- [ ] 🟥 **Scenario 8:** iOS PWA: stop audio mid-segment, background, return → segment highlighted, tap plays from segment start
- [ ] 🟥 **Scenario 9:** iOS PWA: return after 24+ hours → state cleared, starts fresh
- [ ] 🟥 **Scenario 10:** Process new newsletter → segments have individual `audio_url` values

### Acceptance Criteria

- [ ] Tapping a segment plays that segment's audio immediately
- [ ] Current segment is visually highlighted during playback
- [ ] Returning to iOS PWA shows the correct segment highlighted and scrolled into view
- [ ] New newsletters have per-segment audio URLs in database
- [ ] Existing newsletters continue to work (graceful fallback if segment has no audio_url)
