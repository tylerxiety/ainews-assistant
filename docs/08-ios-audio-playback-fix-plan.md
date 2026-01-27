# iOS Voice Q&A Audio Playback Fix

**Overall Progress:** `90%`

## TLDR

Fix the Voice Q&A feature where answer audio fails to play on iOS (Chrome & Safari). The issue is iOS's strict autoplay policy blocking programmatic `play()` calls outside user gesture context. Solution: use a **single audio element** for both newsletter and Q&A audio, leveraging the already-unlocked element.

## Critical Decisions

- **Single audio element**: Use the same `audioRef` for both newsletter and Q&A audio. Since user already "unlocked" it by tapping play, iOS allows subsequent `play()` calls on this element.
- **Exact position restoration**: Store `currentTime` and `src` before switching to Q&A audio, restore after Q&A ends.
- **Fallback button**: If `play()` still fails (edge case), show a "Play Answer" button so user can manually trigger playback with a gesture.
- **No separate QA audio ref**: Remove `qaAudioRef` to simplify and ensure single-element strategy.

## Tasks

- [x] 🟩 **Step 1: Add new state for Q&A audio mode**
  - [x] 🟩 Add `isPlayingQaAudio: boolean` state to track when playing Q&A answer
  - [x] 🟩 Add `savedNewsletterPosition: useRef<number>` to store exact position
  - [x] 🟩 Add `savedNewsletterSrc: useRef<string | null>` to store newsletter audio URL
  - [x] 🟩 Add `qaPlaybackFailed: boolean` state for fallback button trigger

- [x] 🟩 **Step 2: Refactor Q&A audio playback to use main audioRef**
  - [x] 🟩 Remove `qaAudioRef` and its `<audio>` element (lines 28, 471-474)
  - [x] 🟩 Update `useEffect([qaAudioUrl])`: save position/src, pause newsletter, switch src, play
  - [x] 🟩 Handle `play()` rejection: set `qaPlaybackFailed = true` instead of silent catch

- [x] 🟩 **Step 3: Update audio event handlers for Q&A mode**
  - [x] 🟩 Update `handleEnded`: check `isPlayingQaAudio`, if true → restore newsletter and resume
  - [x] 🟩 Remove `handleQaEnded` (no longer needed, merged into `handleEnded`)
  - [x] 🟩 Update `handleTimeUpdate`: only update `currentTime` if not in Q&A mode

- [x] 🟩 **Step 4: Add fallback "Play Answer" button**
  - [x] 🟩 Add button in QA panel that shows when `qaPlaybackFailed === true`
  - [x] 🟩 On click: call `audioRef.current.play()` (this is a user gesture, will work)
  - [x] 🟩 Reset `qaPlaybackFailed = false` after successful play

- [x] 🟩 **Step 5: Update Player.css for fallback button**
  - [x] 🟩 Add `.qa-play-button` styles matching existing design

- [ ] 🟥 **Step 6: Test on iOS**
  - [ ] 🟥 Test full flow: newsletter playing → mic tap → question → answer audio plays → newsletter resumes
  - [ ] 🟥 Test fallback: if auto-play fails, button appears and works
  - [ ] 🟥 Test position restoration: newsletter resumes from exact position
  - [ ] 🟥 Test on both Safari and Chrome on iOS

## Implementation Notes

**Key Code Changes in Player.tsx:**

```typescript
// New state
const [isPlayingQaAudio, setIsPlayingQaAudio] = useState(false)
const [qaPlaybackFailed, setQaPlaybackFailed] = useState(false)
const savedNewsletterPositionRef = useRef<number>(0)
const savedNewsletterSrcRef = useRef<string | null>(null)

// Updated useEffect for qaAudioUrl
useEffect(() => {
  if (qaAudioUrl && audioRef.current) {
    // Save newsletter state
    savedNewsletterPositionRef.current = audioRef.current.currentTime
    savedNewsletterSrcRef.current = audioRef.current.src
    
    // Pause newsletter
    audioRef.current.pause()
    
    // Switch to Q&A audio
    setIsPlayingQaAudio(true)
    audioRef.current.src = qaAudioUrl
    
    const playPromise = audioRef.current.play()
    if (playPromise) {
      playPromise.catch(() => {
        setQaPlaybackFailed(true) // Show fallback button
      })
    }
  }
}, [qaAudioUrl])

// Updated handleEnded
const handleEnded = () => {
  if (isPlayingQaAudio) {
    // Q&A audio finished - restore newsletter
    setIsPlayingQaAudio(false)
    setQaAudioUrl(null)
    
    if (audioRef.current && savedNewsletterSrcRef.current) {
      audioRef.current.src = savedNewsletterSrcRef.current
      audioRef.current.currentTime = savedNewsletterPositionRef.current
      
      if (wasPlayingBeforeQa.current) {
        audioRef.current.play().catch(() => {})
      }
    }
    return
  }
  
  // Normal newsletter ended - advance to next group
  // ... existing logic
}
```

## Not In Scope

- Audio unlock on first page visit (newsletter requires tap to play anyway)
- Retry mechanism for failed playback (single fallback button is sufficient)
- Visual indicator showing Q&A audio is playing (same play/pause UI works)
