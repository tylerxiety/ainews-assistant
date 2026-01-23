# Q&A UX Improvements Plan

**Overall Progress:** `100%`

## TLDR

Two polish items for Voice Q&A:
1. **Freeze progress bar** during Q&A audio playback (show saved newsletter position, not Q&A audio progress)
2. **Smooth resume transition** with configurable delay (1.5s default) + "Resuming newsletter..." message + auto-close Q&A panel

## Critical Decisions

- **Configurable delay**: Store `QA_RESUME_DELAY_MS` in a config file for easy experimentation
- **Save both position and duration**: Save newsletter's `currentTime` AND `duration` before switching to Q&A
- **Block metadata updates during Q&A**: Prevent `handleLoadedMetadata` from updating duration state when Q&A audio loads
- **Auto-close Q&A panel**: Close panel when newsletter resumes (after delay)
- **Visual "Resuming..." state**: Show brief message in Q&A panel during delay before closing

## Tasks

- [x] 🟩 **Step 1: Create frontend config file**
  - [x] 🟩 Create `frontend/src/config.ts` with `QA_RESUME_DELAY_MS = 1500`
  - [x] 🟩 Export config for use in Player.tsx

- [x] 🟩 **Step 2: Fix progress bar freeze during Q&A**
  - [x] 🟩 Add `savedNewsletterDurationRef = useRef<number>(0)` 
  - [x] 🟩 Save duration in `useEffect([qaAudioUrl])` before switching
  - [x] 🟩 Update `handleLoadedMetadata`: skip if `isPlayingQaAudio === true`
  - [x] 🟩 In `handleEnded` (Q&A branch): restore duration state from saved ref

- [x] 🟩 **Step 3: Add resume transition with delay**
  - [x] 🟩 Add `isResumingNewsletter: boolean` state for visual feedback
  - [x] 🟩 In `handleEnded` (Q&A branch): set `isResumingNewsletter = true`, then use `setTimeout` with config delay
  - [x] 🟩 After delay: restore src/position, play, set `isResumingNewsletter = false`, close Q&A panel

- [x] 🟩 **Step 4: Update Q&A panel UI for resume state**
  - [x] 🟩 Show "Resuming newsletter..." message when `isResumingNewsletter === true`
  - [x] 🟩 Add CSS for `.qa-resuming` state (subtle styling)

- [x] 🟩 **Step 5: Test**
  - [x] 🟩 Verify progress bar stays frozen at xx/total during Q&A
  - [x] 🟩 Verify 1.5s delay before newsletter resumes
  - [x] 🟩 Verify Q&A panel auto-closes after resume
  - [x] 🟩 Test on iOS Safari/Chrome (Pushed to prod for verification)

## Implementation Notes

**Config file (`frontend/src/config.ts`):**
```typescript
// Q&A feature configuration
export const QA_CONFIG = {
  /** Delay in ms before resuming newsletter after Q&A answer ends */
  RESUME_DELAY_MS: 1500,
}
```

**Key changes in `handleEnded`:**
```typescript
const handleEnded = () => {
  if (isPlayingQaAudio) {
    setIsPlayingQaAudio(false)
    setQaAudioUrl(null)
    setQaPlaybackFailed(false)
    setIsResumingNewsletter(true)  // Show "Resuming..." message

    // Delay before resuming
    setTimeout(() => {
      if (audioRef.current && savedNewsletterSrcRef.current) {
        audioRef.current.src = savedNewsletterSrcRef.current
        audioRef.current.currentTime = savedNewsletterPositionRef.current
        setDuration(savedNewsletterDurationRef.current)  // Restore duration

        if (wasPlayingBeforeQa.current) {
          audioRef.current.play().catch(() => {})
        }
      }
      setIsResumingNewsletter(false)
      setShowQaPanel(false)  // Auto-close
    }, QA_CONFIG.RESUME_DELAY_MS)

    return
  }
  // ... rest unchanged
}
```

**Key changes in `handleLoadedMetadata`:**
```typescript
const handleLoadedMetadata = () => {
  // Don't update duration during Q&A playback
  if (audioRef.current && !isPlayingQaAudio) {
    setDuration(audioRef.current.duration)
  }
}
```

## Not In Scope

- Audio chime/beep for transition (possible future enhancement)
- Customizable resume message text
- Non-auto-close option
