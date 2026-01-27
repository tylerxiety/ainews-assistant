# UI/UX Redesign Plan

**Overall Progress:** `95%`

## TLDR

Redesign the player from a card-based "app" feel to a clean, flowing newsletter reading experience on mobile. Remove segment cards, add a left side panel with TOC + Q&A tabs, migrate colors from purple to black + orange, replace emoji icons with Lucide, and change Q&A scope from per-topic to whole-newsletter.

## Critical Decisions

- **Flowing text over cards**: Segments render as continuous text with orange left-border on active segment (no card backgrounds/borders)
- **Left side panel**: Single drawer with two tabs (Contents + Q&A), ~80% viewport width, replaces both segment counter and Q&A overlay
- **Three audio bar buttons**: Mic (record), Q&A (view history), TOC (navigation) — each has a distinct purpose
- **Mic opens Q&A panel after answer**: Tap mic starts recording; Q&A panel auto-opens once the answer arrives
- **Inline links**: Link pills replaced with inline underlined `<a>` tags matched within `content_raw`
- **Whole-newsletter Q&A scope**: Backend queries all segments by `issue_id` instead of filtering by `topic_group_id`
- **Component extraction**: Player.tsx split into AudioBar, SegmentList, SidePanel sub-components (enables parallel work)
- **lucide-react for icons**: Replace all emoji Unicode icons with Lucide components
- **CSS custom properties**: Centralized color tokens in `:root`, dark mode only

## Context for Agents

### Project Stack
- **Frontend**: Vite + React 19 + TypeScript, plain CSS (no Tailwind), deployed on Vercel as PWA
- **Backend**: Python FastAPI on Google Cloud Run, Supabase (Postgres), GCS for audio
- **No icon library** currently (all emoji), **no CSS variables** (all hardcoded hex)

### Key Files

| File | Purpose |
|---|---|
| `frontend/src/components/Player.tsx` (769 lines) | Main player — all rendering + state in one component |
| `frontend/src/components/Player.css` (688 lines) | All player styles |
| `frontend/src/types.ts` | TypeScript interfaces (Issue, Segment, TopicGroup, ConversationMessage) |
| `frontend/src/index.css` | Global styles, `:root` font settings |
| `frontend/src/hooks/useAudioRecorder.ts` | MediaRecorder hook for voice Q&A |
| `frontend/src/hooks/usePlaybackState.ts` | Playback position persistence |
| `frontend/src/lib/supabase.ts` | Supabase client + data fetching |
| `frontend/src/lib/api.ts` | API URL helper (`apiUrl()`) |
| `frontend/src/config.ts` | Frontend config loader (from config.yaml) |
| `backend/main.py` | FastAPI endpoints including `POST /ask-audio` |
| `backend/processor.py` | Newsletter processing + `ask_with_audio()` Q&A logic |
| `config.yaml` | Shared config (frontend + backend), includes Q&A prompt |

### Data Model
```
Issue
 TopicGroup[] (ordered by order_index)
     label: string (e.g., "Frontier model governance")
     Segment[] (ordered by order_index)
         content_raw: string (display text)
         links: [{text, url}] (extracted URLs, rendered as pills currently)
         audio_url: string (per-segment GCS audio)
         segment_type: 'section_header' | 'item' | 'topic_header'
```

### Current Audio Bar
```
[Play/Pause] [ProgressBar] [Time] [Speed] [Mic] [SegmentCounter "4/4"]
```
Mobile: progress bar wraps to second row via flex-wrap + order:5.

### Current Q&A Flow
1. Frontend sends FormData (`audio` blob, `issue_id`, `group_id`) to `POST /ask-audio`
2. Backend (`processor.py:590-604`) queries segments by `topic_group_id`, builds context text
3. Gemini transcribes audio + answers, returns `{answer, audio_url, transcript}`
4. Frontend shows Q&A in fixed overlay panel above audio bar (`Player.tsx:645-694`, `Player.css:548-688`)

### Current Colors (to replace)
- Accent: `#646cff` (purple) — play button, links, progress, active states, hover borders
- Backgrounds: `#242424` (root), `#1a1a1a` (cards/controls), `#252525` (hover/panel)
- Text: `#f0f0f0` (primary), `#d0d0d0` (body), `#888` (muted)
- Borders: `#333` (default), `#444` (input)

## Module Dependency Graph

```
Module 0 (Foundation) ---- must complete first
   Module 1 (Segments)     -+
   Module 2 (Audio Bar)     +-- can run in parallel after Module 0
   Module 3 (Side Panel)   -+
   Module 4 (Colors)       ---- can run with 1/2/3 or after

Module 5 (Backend Q&A)     ---- fully independent, can start anytime
```

## Tasks

- [x] 🟩 **Module 0: Foundation (extract components + setup)**
  - [x] 🟩 Install `lucide-react`: `cd frontend && npm install lucide-react`
  - [x] 🟩 Add CSS custom properties to `frontend/src/index.css` `:root` block:
    - `--color-accent: #f97316` (orange), `--color-accent-hover: #ea580c`, `--color-accent-muted: rgba(249,115,22,0.1)`, `--color-accent-muted-hover: rgba(249,115,22,0.2)`
    - `--color-bg-root: #242424`, `--color-bg-surface: #1a1a1a`, `--color-bg-elevated: #252525`, `--color-bg-active: #2a1a0a`
    - `--color-text-primary: #f0f0f0`, `--color-text-secondary: #d0d0d0`, `--color-text-muted: #888`, `--color-text-dimmed: #666`
    - `--color-border: #333`, `--color-border-input: #444`
    - `--color-success: #4ade80`, `--color-error: #f87171`, `--color-warning: #facc15`
  - [x] 🟩 Create `frontend/src/components/SegmentList.tsx` + `SegmentList.css` — extract segment rendering (Player.tsx lines 696-765) and segment styles (Player.css lines 139-505). Props interface:
    ```typescript
    interface SegmentListProps {
      groups: TopicGroup[]
      currentGroupIndex: number
      currentSegmentIndex: number
      bookmarkedSegments: Set<string>
      bookmarkingSegment: string | null
      onSegmentClick: (groupIndex: number, segmentIndex: number) => void
      onBookmark: (e: React.MouseEvent, segment: Segment) => void
    }
    ```
  - [x] 🟩 Create `frontend/src/components/AudioBar.tsx` + `AudioBar.css` — extract audio controls (Player.tsx lines 607-643) and styles (Player.css lines 56-137, 507-546). Props interface:
    ```typescript
    interface AudioBarProps {
      isPlaying: boolean
      currentTime: number
      duration: number
      playbackSpeed: number
      isRecording: boolean
      onPlayPause: () => void
      onProgressClick: (e: React.MouseEvent<HTMLDivElement>) => void
      onSpeedCycle: () => void
      onMicClick: () => void
      onOpenToc: () => void
      onOpenQa: () => void
      disabled: boolean
    }
    ```
  - [x] 🟩 Create `frontend/src/components/SidePanel.tsx` + `SidePanel.css` — new component (empty shell for now, will be filled in Module 3). Props interface:
    ```typescript
    interface SidePanelProps {
      isOpen: boolean
      activeTab: 'toc' | 'qa'
      onClose: () => void
      onTabChange: (tab: 'toc' | 'qa') => void
      groups: TopicGroup[]
      currentGroupIndex: number
      onGroupSelect: (groupIndex: number) => void
      messages: ConversationMessage[]
      isRecording: boolean
      isLoadingAnswer: boolean
      recorderError: string | null
      isResumingNewsletter: boolean
      qaPlaybackFailed: boolean
      onPlayQaManually: () => void
    }
    ```
  - [x] 🟩 Refactor `Player.tsx` to orchestrator — keep all state + handlers + `<audio>` element, render child components via props. Add new state: `sidePanelOpen`, `sidePanelTab`. Remove old QA panel JSX (lines 645-694). Replace `showQaPanel` with `sidePanelOpen`/`sidePanelTab`. Add handlers: `handleOpenToc`, `handleOpenQa`, `handleGroupSelect`.
  - [x] 🟩 Verify: `npm run build` passes, app looks and behaves identically to before (pure refactor)

- [x] 🟩 **Module 1: Segment Redesign** (after Module 0)
  - Files: `frontend/src/components/SegmentList.tsx`, `frontend/src/components/SegmentList.css`
  - [x] 🟩 Remove card styling from `.segment` / `.group-item`: delete `background`, `border`, `border-radius`. Segments should be plain text blocks.
  - [x] 🟩 Reduce gap between segments from `20px` to `8-12px` for continuous prose feel.
  - [x] 🟩 Active segment: 3px orange left-border + subtle bg tint: `border-left: 3px solid var(--color-accent); padding-left: 12px; background: var(--color-bg-active);`
  - [x] 🟩 Bookmark icon: only render on active segment. Replace emoji (`📌` `✓` `⏳`) with Lucide icons (`Pin`, `Check`, `Loader2`).
  - [x] 🟩 Inline links: create `renderContentWithLinks(content: string, links: SegmentLink[]): ReactNode` helper. Match each `link.text` in `content` and replace with `<a href={link.url}>` (underlined, orange). Fallback: if `link.text` not found in content, append as standalone link.
  - [x] 🟩 Group titles: add `id={`group-${group.id}`}` attribute for TOC scroll-to linking.

- [x] 🟩 **Module 2: Audio Bar Redesign** (after Module 0)
  - Files: `frontend/src/components/AudioBar.tsx`, `frontend/src/components/AudioBar.css`
  - [x] 🟩 New two-row layout: Row 1 = `[Play/Pause] [Time] [Speed] [Mic] [Q&A] [TOC]`, Row 2 = full-width progress bar (always, not just mobile).
  - [x] 🟩 Replace emoji with Lucide icons: `Play`/`Pause` (play button), `Mic` (mic button), `MessageSquareText` (Q&A button), `List` (TOC button).
  - [x] 🟩 Colors: play button `background: var(--color-accent)` (orange) with white icon; other buttons transparent with `var(--color-text-primary)` icon color; progress bar fill `var(--color-accent)`.
  - [x] 🟩 Remove segment counter span (`.segment-indicator`). TOC button replaces it.
  - [x] 🟩 Wire button callbacks: `onOpenToc`, `onOpenQa`, `onMicClick`.

- [x] 🟩 **Module 3: Side Panel — TOC + Q&A** (after Module 0)
  - Files: `frontend/src/components/SidePanel.tsx`, `frontend/src/components/SidePanel.css`, `frontend/src/components/Player.tsx`
  - [x] 🟩 Side panel shell: left-sliding drawer, `width: 80vw; max-width: 400px`, `position: fixed; top:0; left:0; bottom:0`. Scrim overlay (`rgba(0,0,0,0.5)`) covers remaining viewport, tap to dismiss. Slide-in animation via CSS `transform: translateX` (~200ms).
  - [x] 🟩 Tab bar at top: "Contents" and "Q&A" buttons, orange underline on active tab.
  - [x] 🟩 TOC tab: scrollable list of `groups[].label`. Current group highlighted orange. On tap: call `onGroupSelect(groupIndex)` which sets group/segment indices, enables autoplay, scrolls to `#group-{id}`, and closes panel.
  - [x] 🟩 Q&A tab: move existing Q&A message rendering here. User messages right-aligned (orange bg), assistant messages left-aligned (gray bg). Empty state: "Ask a question using the mic button." Loading states: "Recording...", "Thinking...", "Resuming newsletter..."
  - [x] 🟩 Player.tsx wiring: after Q&A answer arrives in `handleAskQuestionWithAudio`, set `setSidePanelOpen(true)` and `setSidePanelTab('qa')` to auto-open panel.

- [x] 🟩 **Module 4: Color Migration** (after Modules 1-3)
  - Files: all `.css` files in `frontend/src/`
  - [x] 🟩 Replace `#646cff` with `var(--color-accent)` and `#535bf2` with `var(--color-accent-hover)` across all CSS files
  - [x] 🟩 Replace hardcoded backgrounds: `#242424` → `var(--color-bg-root)`, `#1a1a1a` → `var(--color-bg-surface)`, `#252525` → `var(--color-bg-elevated)`
  - [x] 🟩 Replace text colors: `#f0f0f0` → `var(--color-text-primary)`, `#d0d0d0`/`#d4d4d8` → `var(--color-text-secondary)`, `#888` → `var(--color-text-muted)`, `#666` → `var(--color-text-dimmed)`
  - [x] 🟩 Replace borders: `#333` → `var(--color-border)`, `#444` → `var(--color-border-input)`
  - [x] 🟩 Replace `rgba(100, 108, 255, ...)` purple tints → `var(--color-accent-muted)` / `var(--color-accent-muted-hover)`
  - [x] 🟩 Remove `@media (prefers-color-scheme: light)` block in `index.css` (lines 58-69) — dark mode only
  - [x] 🟩 Check: also update `Settings.css`, `IssueList.css`, `Loading.css` if they contain hardcoded colors

- [x] 🟩 **Module 5: Backend Q&A Scope Change** (independent)
  - [x] 🟩 `backend/main.py` (lines 74-98): remove `group_id: str = Form(...)` parameter from `/ask-audio` endpoint, update call to `processor.ask_with_audio(audio, issue_id)`
  - [x] 🟩 `backend/processor.py` (lines 551-672): update `ask_with_audio()` — remove `group_id` parameter, change segment query from `.eq("topic_group_id", group_id)` to `.eq("issue_id", issue_id)`
  - [x] 🟩 `config.yaml` (lines 73-89): update Q&A prompt — change "a section" to "a newsletter"
  - [x] 🟩 `frontend/src/components/Player.tsx`: remove `formData.append('group_id', groups[currentGroupIndex].id)` from `handleAskQuestionWithAudio()`

## Testing (Required)

### Approach
Manual browser testing (DevTools mobile view or real device) + `npm run build` for type safety.

### Test Scenarios
- [ ] 🟥 Segments display: Open a newsletter — segments render as flowing text without card borders, group titles visible as section headers
- [ ] 🟥 Active segment: Tap a segment — orange left-border appears, bookmark icon shows, audio starts playing
- [ ] 🟥 Inline links: Links within segment text are underlined and clickable, open in new tab
- [ ] 🟥 Audio bar: All 6 controls visible (Play, Time, Speed, Mic, Q&A, TOC) + progress bar on second row. No emoji — all Lucide icons.
- [ ] 🟥 TOC panel: Tap TOC button — left panel slides in showing group labels. Current group highlighted orange. Tap a group — scrolls to section, starts playback, panel closes.
- [ ] 🟥 Q&A panel: Tap Q&A button — left panel opens to Q&A tab showing message history (or empty state)
- [ ] 🟥 Voice Q&A: Tap mic — recording starts. Stop recording — Q&A panel auto-opens with "Thinking..." then answer appears. TTS audio plays. Newsletter resumes after.
- [ ] 🟥 Q&A scope: Ask about content from a different topic group than currently playing — answer should reference it correctly (whole-newsletter context)
- [ ] 🟥 Bookmark: Tap active segment pin icon — bookmark created in ClickUp, icon changes to checkmark
- [ ] 🟥 Color: No purple (`#646cff`) visible anywhere. All accents are orange. Text readable on all backgrounds.
- [ ] 🟥 Playback continuity: Play through multiple segments — auto-advance to next segment and next group works. Speed control persists.
- [ ] 🟥 Panel dismiss: Tap scrim area outside side panel — panel closes

### Acceptance Criteria
- [ ] `npm run build` completes with zero TypeScript errors
- [ ] No `#646cff` or `#535bf2` present in any CSS file (verified by grep)
- [ ] No emoji icons (`▶`, `⏸`, `🎤`, `📌`, `⚙️`) in Player, AudioBar, SegmentList components
- [ ] Audio resumes from saved position after Q&A TTS ends
- [ ] TOC items match `groups[].label` values and scroll to correct `#group-{id}` elements
- [ ] Side panel width is ~80vw (max 400px) with visible scrim overlay
- [ ] Backend `/ask-audio` endpoint no longer requires `group_id` parameter

## Execution Strategy

**Group 1** (sequential, first): Module 0
**Group 2** (parallel, after Module 0):
- Agent A: Module 1 (SegmentList files only)
- Agent B: Module 2 + 3 (AudioBar + SidePanel + Player.tsx wiring — shared interaction)
- Agent C: Module 5 (backend, fully independent)
**Group 3** (after Group 2): Module 4 (color sweep across all CSS)
