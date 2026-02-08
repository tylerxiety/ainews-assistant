# Feature Implementation Plan

**Overall Progress:** `100%`

## TLDR
Fix newsletter text extraction corruption (missing spaces), then apply conservative section consolidation: keep Twitter unchanged, keep only `AI Discord Recap`, and lightly deduplicate Reddit content for future issues only.

## Critical Decisions
Key architectural/implementation choices made during exploration:
- Decision 1: Keep only `AI Discord Recap` for Discord content - removes repeated Discord layers while preserving top summary value.
- Decision 2: Apply light Reddit dedup only - reduce repetition without aggressive summarization risk.
- Decision 3: Roll out to future issues first - minimizes risk before optional backfill.

## Tasks:

- [x] 🟩 **Step 1: Fix parser text-boundary corruption**
  - [x] 🟩 Replace current HTML text extraction with spacing-preserving extraction in newsletter parsing.
  - [x] 🟩 Add normalization to avoid doubled spaces while preserving readable punctuation boundaries.
  - [x] 🟩 Verify sample corrupted strings no longer appear (e.g., `BASI JailbreakingDiscord`, `Twittersand`).

- [x] 🟩 **Step 2: Add section-aware filtering and light consolidation**
  - [x] 🟩 Add section tracking in parse/group pipeline to identify Twitter/Reddit/Discord regions.
  - [x] 🟩 Keep Twitter path unchanged.
  - [x] 🟩 Keep only `AI Discord Recap` section content and skip `Discord: High level...` + `Discord: Detailed...`.
  - [x] 🟩 Apply light Reddit dedup in processing (remove near-duplicate items/topics, keep structure intact).

- [x] 🟩 **Step 3: Add config controls in `config.yaml`**
  - [x] 🟩 Add explicit toggles for section consolidation behavior (Discord mode + Reddit light dedup enablement).
  - [x] 🟩 Default config to selected policy (Twitter unchanged, Discord A, Reddit A).
  - [x] 🟩 Ensure backend reads config centrally with safe defaults.

- [x] 🟩 **Step 4: Verification and rollout guardrails**
  - [x] 🟩 Run processing against one recent issue and inspect produced groups/segments for section correctness.
  - [x] 🟩 Confirm no regression in playback assumptions (group ordering, section headers, per-segment audio).
  - [x] 🟩 Ship for future issues only (no backfill job execution in this phase).

## Testing (Required)

### Approach
API/script validation (`uv run` in backend), targeted parser assertions, and manual data inspection of generated groups/segments.

### Test Scenarios
- [x] 🟩 Scenario 1: Process `https://news.smol.ai/issues/26-02-06-not-much` → Discord headings keep spaces and remain readable.
- [x] 🟩 Scenario 2: Process a recent issue with all three sections → Twitter remains unchanged, Discord only includes `AI Discord Recap`, Reddit keeps structure with reduced duplicate items.
- [x] 🟩 Scenario 3: Process issue with sparse/missing section patterns → parser does not fail and preserves available content safely.

### Acceptance Criteria
- [x] Parsed/processed output no longer contains concatenation artifacts like `AIDiscord`, `Twittersand`, or `JailbreakingDiscord` for tested issues.
- [x] Final stored groups contain Twitter section intact, Discord reduced to `AI Discord Recap` only, and Reddit duplicates reduced without collapsing section structure.
- [x] Processing pipeline completes successfully with existing playback model (single `<audio>`, per-segment audio, topic group ordering) unchanged.

## Output Location

Saved to `docs/15-discord-reddit-consolidation-plan.md`.
