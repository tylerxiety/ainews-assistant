# Segment Playback & PWA State Persistence Plan

**Overall Progress:** `100%`

## TLDR

Two UI improvements:
1. **Per-segment playback:** Users can tap individual segments to play them (not just whole topics). Requires switching from combined group audio to per-segment audio files.
2. **State persistence (mobile + desktop):** When the app is backgrounded or the user navigates away and returns, restore the user's position (highlight + scroll to last segment), without resuming mid-segment.

## Critical Decisions

- **Per-segment audio files:** Generate one TTS call per segment.
- **localStorage-only for state:** No URL changes. Store `{ issueId, groupIndex, segmentIndex, savedAt }`.
- **Resume granularity:** Segment start only (no mid-segment resume).
- **No fallback to group audio:** Per-segment audio is required. Old issues without segment audio are not expected to play.
- **New newsletters only:** No migration of existing data; changes apply to newly processed issues.
- **Navigation behavior:** "Navigate away" means SPA route changes (e.g., Home/Settings) that unmount the Player, not a full page reload.
- **Platform parity:** Same persistence behavior on desktop and mobile.
- **Expiration:** 24 hours, configurable in `config.yaml`.

## Tasks

### Backend Changes

- [x] 🟩 **Step 1: Database schema update**
  - [x] 🟩 Add `audio_url` (text, nullable) to `segments` table
  - [x] 🟩 Add `audio_duration_ms` (integer, nullable) to `segments` table

- [x] 🟩 **Step 2: Update processor for per-segment audio**
  - [x] 🟩 Modify `_generate_audio` to accept group + segment indices for deterministic blob naming
  - [x] 🟩 Update `process_group` to generate audio per segment (not combined)
  - [x] 🟩 Store `audio_url` and `audio_duration_ms` on each segment
  - [x] 🟩 Remove group-level audio generation (set `audio_url` on group to null)

### Frontend Changes

- [x] 🟩 **Step 3: Update types and data fetching**
  - [x] 🟩 Add `audio_url` and `audio_duration_ms` to `Segment` type
  - [x] 🟩 Ensure `fetchIssueWithGroups` returns segment audio fields

- [x] 🟩 **Step 4: Per-segment playback in Player**
  - [x] 🟩 Add `currentSegmentIndex` state alongside `currentGroupIndex`
  - [x] 🟩 Add `handleSegmentClick(groupIndex, segmentIndex)` handler
  - [x] 🟩 Update audio source logic to use `segment.audio_url` only (no group fallback)
  - [x] 🟩 On audio end: advance to next segment, or next group if last segment
  - [x] 🟩 Highlight current segment (CSS class `active` on segment)
  - [x] 🟩 Auto-scroll to current segment (not just group)

- [x] 🟩 **Step 5: PWA state persistence**
  - [x] 🟩 Add `playbackStateExpirationMs` to `config.yaml` (default: 24 hours in ms)
  - [x] 🟩 Create `usePlaybackState` hook or inline logic:
    - [x] 🟩 Save state to localStorage on `visibilitychange` (hidden), `beforeunload`, and Player unmount (SPA navigation)
    - [x] 🟩 Save: `{ issueId, groupIndex, segmentIndex, savedAt }`
  - [x] 🟩 On Player mount: restore state if valid (same issueId, not expired)
  - [x] 🟩 On restore: set `currentGroupIndex`, `currentSegmentIndex`, scroll to segment, highlight
  - [x] 🟩 Clear saved state when newsletter finishes

- [x] 🟩 **Step 6: Differentiate tap vs scroll on segments**
  - [x] 🟩 Track pointer position on `pointerdown`
  - [x] 🟩 On `pointerup`, only trigger playback if movement < threshold (e.g., 10px)
  - [x] 🟩 Ensure links and bookmark buttons still work via `stopPropagation`

### Config Changes

- [x] 🟩 **Step 7: Add config entries**
  - [x] 🟩 Add `playbackStateExpirationMs: 86400000` to `config.yaml` (frontend section)
  - [x] 🟩 Expose in frontend `CONFIG` object

## Testing (Required)

### Approach
Use browser agent or MCP tools for testing on iOS PWA and desktop Chrome.

### Test Scenarios

- [x] 🟩 **Scenario 1:** Tap segment in current group → audio plays from that segment's start
- [x] 🟩 **Scenario 2:** Tap segment in different group → switches group, plays that segment
- [x] 🟩 **Scenario 3:** Segment ends → next segment in group auto-plays
- [x] 🟩 **Scenario 4:** Last segment in group ends → first segment of next group auto-plays
- [x] 🟩 **Scenario 5:** Last segment of last group ends → playback stops, no crash
- [x] 🟩 **Scenario 6:** Scroll through segments without triggering playback
- [x] 🟩 **Scenario 7:** iOS PWA: playing audio, background app, return → audio continues, correct segment highlighted and visible
- [x] 🟩 **Scenario 8:** iOS PWA: stop audio mid-segment, background, return → segment highlighted, tap plays from segment start
- [x] 🟩 **Scenario 9:** iOS PWA: return after 24+ hours → state cleared, starts fresh
- [x] 🟩 **Scenario 10:** SPA nav: go to Home/Settings and back within 24h → segment highlight restored
- [x] 🟩 **Scenario 11:** Desktop: same persistence behavior as mobile (restore highlight, no mid-segment resume)
- [x] 🟩 **Scenario 12:** Process new newsletter → segments have individual `audio_url` values

### Acceptance Criteria

- [x] Tapping a segment plays that segment's audio immediately
- [x] Current segment is visually highlighted during playback
- [x] Returning to iOS PWA shows the correct segment highlighted and scrolled into view
- [x] New newsletters have per-segment audio URLs in database
- [x] No fallback to group audio; per-segment audio is required for playback
