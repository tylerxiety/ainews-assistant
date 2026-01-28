# Voice Command & Q&A via Gemini Live API

**Overall Progress:** `85%`

## TLDR

Add a tap-to-enable voice mode to the PWA. While the newsletter plays, users can speak commands (play, pause, next, previous, bookmark, rewind, forward) or ask Q&A questions — all hands-free. Playback pauses on speech, resumes after handling. Uses Gemini Live API with function calling through a backend WebSocket proxy (iOS Safari compatibility). Client-side VAD for instant speech detection. AudioContext for mic capture (PCM) and streaming Q&A audio playback. Newsletter stays on `<audio>`; Q&A audio plays via AudioContext.

## Critical Decisions

- **Server-side proxy**: Browser → FastAPI WebSocket → Gemini Live (avoids iOS 26 Safari WebSocket upgrade bug with GCP endpoints)
- **Client-side VAD (Silero via @ricky0123/vad-web)**: Pause newsletter instantly on speech start; Gemini Live has no `speech_started` event
- **Function calling for commands**: Define play/pause/next/etc. as Gemini tools — no custom classifier needed. Anything not a command gets a Q&A audio response
- **AudioContext for all voice I/O**: Mic capture as 16kHz PCM (Gemini input format), Q&A playback as 24kHz PCM (Gemini output format). `<audio>` element stays for newsletter MP3s only
- **AUDIO-only responses + transcripts**: Session uses `response_modalities: ["AUDIO"]`. Use real-time audio transcripts from the API as the answer text in the Q&A panel; show question text as `[user question]`
- **No wake word**: Tap-to-enable toggle is the activation gesture
- **Silent visual feedback for commands**: No spoken confirmation — newsletter resumes immediately
- **One Gemini Live session per issue**: Newsletter context in system prompt at session start. Handle connection reset (~10 min) and 15-min session limit with resumption tokens
- **Keep existing Q&A flow as fallback**: If voice mode WebSocket fails, existing mic-button Q&A still works
- **Vertex AI backend**: Use `google-genai` SDK configured for Vertex AI (ADC, project, location `us-central1`)

## Context for Implementer

- **Existing Q&A flow**: `frontend/src/components/Player.tsx` swaps the `<audio>` element to play Q&A audio and restores newsletter state. Voice mode must not break this fallback path.
- **Mic recording hook**: `frontend/src/hooks/useAudioRecorder.ts` handles manual Q&A (MediaRecorder); voice mode should disable/replace mic button while active.
- **Config source of truth**: All settings live in `config.yaml` (frontend consumes via `frontend/src/config.ts`, backend via `backend/config.py`).
- **Backend deps**: Python deps are managed in `backend/pyproject.toml` with `uv` (no `requirements.txt` updates).
- **iOS constraints**: AudioContext must be created on user tap; keep newsletter playback on `<audio>` element.

## Tasks

- [x] 🟩 **Step 1: Backend — Gemini Live WebSocket proxy**
  - [x] 🟩 Add `google-genai` to `backend/pyproject.toml` dependencies (uv-managed)
  - [x] 🟩 Create `backend/voice_session.py` — manages one Gemini Live session per WebSocket connection
    - Connect to Gemini Live (`gemini-live-2.5-flash-native-audio`) via `google-genai` SDK configured for Vertex AI (`project`, `location`)
    - Configure session: system prompt with newsletter context, response modalities `["AUDIO"]`
    - Define function tools: `play`, `pause`, `next_segment`, `previous_segment`, `bookmark`, `rewind(seconds=5)`, `forward(seconds=5)`
    - Forward incoming PCM audio chunks from client → Gemini Live session
    - Receive Gemini responses: forward tool calls as JSON, forward audio chunks as binary, forward answer transcripts as JSON
    - Handle connection reset (~10 min) + session expiry (~15 min) with resumption tokens
  - [x] 🟩 Add WebSocket endpoint `ws /ws/voice/{issue_id}` in `main.py`
    - On connect: fetch newsletter context from Supabase, open Gemini Live session
    - Bidirectional relay: client audio → Gemini, Gemini responses → client
    - On disconnect: close Gemini Live session, cleanup
  - [x] 🟩 Add `voiceMode` config section to `config.yaml` (model name, region, session timeout, VAD sensitivity, resume delay)

- [x] 🟩 **Step 2: Frontend — AudioContext mic capture + PCM streaming**
  - [x] 🟩 Create `frontend/src/hooks/useVoiceMode.ts` — core voice mode hook
    - Open WebSocket to `/ws/voice/{issueId}`
    - Create `AudioContext` (on user tap gesture)
    - Capture mic via `getUserMedia` → `AudioWorkletNode` → downsample to 16kHz mono PCM
    - Stream PCM chunks over WebSocket as binary messages
    - Receive WebSocket messages: parse JSON (tool calls) vs binary (audio response chunks)
    - Expose state: `isVoiceModeActive`, `isListening`, `isSpeaking` (from VAD), `lastCommand`
    - Handle reconnection on session expiry
  - [x] 🟩 Create `frontend/src/worklets/pcm-capture.worklet.ts` — AudioWorklet processor
    - Capture mic audio, resample to 16kHz if needed, output Int16 PCM chunks
  - [x] 🟩 Add `@ricky0123/vad-web` dependency to `package.json`

- [x] 🟩 **Step 3: Frontend — Client-side VAD integration**
  - [x] 🟩 Integrate Silero VAD in `useVoiceMode.ts`
    - On `onSpeechStart`: pause `<audio>` newsletter immediately, signal "user speaking" state
    - On `onSpeechEnd`: if Gemini returns a tool call → resume newsletter after command execution; if Q&A audio response → resume after playback ends
    - Configure sensitivity thresholds (from config)

- [x] 🟩 **Step 4: Frontend — Q&A audio playback via AudioContext**
  - [x] 🟩 Add playback logic in `useVoiceMode.ts`
    - Receive 24kHz PCM chunks from WebSocket
    - Queue and play via `AudioContext` using `AudioBufferSourceNode` (streaming: schedule sequential buffers)
    - Track playback completion — trigger newsletter resume after last chunk plays
  - [x] 🟩 Handle AudioContext suspension/resumption on iOS (re-resume on user interaction if suspended)

- [x] 🟩 **Step 5: Frontend — Command execution bridge**
  - [x] 🟩 Wire tool call JSON from WebSocket to Player.tsx actions
    - `play` → `handlePlay()`
    - `pause` → `handlePause()`
    - `next_segment` → advance to next segment (reuse existing `handleEnded` auto-advance logic)
    - `previous_segment` → go to previous segment
    - `bookmark` → trigger bookmark on current segment (reuse existing bookmark handler)
    - `rewind(seconds)` → `audioRef.current.currentTime -= seconds`
    - `forward(seconds)` → `audioRef.current.currentTime += seconds`
  - [x] 🟩 Add visual feedback for commands — brief toast or icon flash in AudioBar (e.g., "Bookmarked" toast, rewind icon animation)

- [x] 🟩 **Step 6: Frontend — Voice mode UI**
  - [x] 🟩 Add voice mode toggle button to AudioBar (replace or augment existing mic button)
    - Inactive: mic icon (current)
    - Active: pulsing/glowing mic icon + "Listening" indicator
    - Tap toggles voice mode on/off
  - [x] 🟩 Update SidePanel Q&A tab to show voice mode state
    - Show real-time status: "Listening...", "Processing...", command executed feedback
    - Q&A messages still appear in conversation history (from Gemini Live audio transcripts)
    - Question text is shown as `[user question]` for voice mode
  - [x] 🟩 Add voice mode active indicator in AudioBar (subtle persistent indicator when mode is on)

- [x] 🟩 **Step 7: Config and integration**
  - [x] 🟩 Add voice mode config to `config.yaml` and `frontend/src/config.ts`
    - `voiceMode.model` = `gemini-live-2.5-flash-native-audio`
    - `voiceMode.region` = `us-central1`
    - `voiceMode.sessionTimeoutMs`, `voiceMode.vadSensitivity`
    - `voiceMode.resumeDelayMs` (delay before resuming newsletter after Q&A)
  - [x] 🟩 Update Player.tsx to integrate `useVoiceMode` hook
    - Pass command handlers to the hook
    - Coordinate voice mode state with existing Q&A state (voice mode replaces manual Q&A when active)
    - Handle edge cases: voice mode + manual mic button, voice mode during segment transitions

## Testing

**Test Notes (2026-01-28):** Playwright on ngrok failed to load `silero_vad.onnx` (protobuf parsing error), so voice mode could not start. Remaining scenarios blocked.

### Approach
Test on iOS Safari PWA + Chrome desktop using browswer agent. Backend WebSocket tested via Python WebSocket client script.

### Test Scenarios
- [ ] 🟥 Tap voice mode toggle → WebSocket connects, mic access granted, "Listening" indicator shown
- [ ] 🟥 Say "pause" while newsletter plays → newsletter pauses within 200ms of speech start (VAD), Gemini returns `pause` tool call, visual feedback shown
- [ ] 🟥 Say "play" while paused → newsletter resumes from saved position
- [ ] 🟥 Say "next" → advances to next segment, plays from start
- [ ] 🟥 Say "bookmark" → current segment bookmarked, toast shown, newsletter resumes
- [ ] 🟥 Say "rewind" → currentTime decreases by 5 seconds, newsletter resumes
- [ ] 🟥 Ask a question (e.g., "What did they say about React?") → newsletter pauses, Gemini responds with audio, audio plays through AudioContext, newsletter resumes after answer
- [ ] 🟥 Tap voice mode toggle off → WebSocket closes, mic released, indicator removed
- [ ] 🟥 Session expires (15 min) → auto-reconnects with resumption token, no user-visible interruption
- [ ] 🟥 iOS Safari PWA: voice mode works with screen on, AudioContext not suspended during active use
- [ ] 🟥 Voice mode off → existing mic-button Q&A flow still works unchanged

### Acceptance Criteria
- [ ] Voice commands execute and newsletter resumes within 500ms of speech end (excluding network latency)
- [ ] Newsletter audio pauses within 200ms of user starting to speak (client-side VAD)
- [ ] Q&A audio response streams and plays without audible gaps or artifacts
- [ ] Newsletter resumes from exact saved position after command or Q&A
- [ ] Voice mode toggle is a single tap — no multi-step activation
- [ ] Existing non-voice Q&A flow (mic button → record → stop → answer) works when voice mode is off
- [ ] No microphone access requested until user taps voice mode toggle
- [ ] Works on iOS Safari PWA in foreground with screen on

## Implementation Notes (Deviations)

- **Command handling**: Added server-side command detection from input audio transcription and suppress model output for those turns, instead of relying solely on Gemini tool calls. Reason: model occasionally answered with Q&A (“let me check”) for command words like “next,” so commands were dropped.
- **Tool set**: Removed `next_segment`/`previous_segment` tool declarations and standardized on `next`/`previous` only. Reason: user requirement that only play/pause/next/previous/bookmark/rewind/forward are tools.
- **State handling**: Voice command segment navigation now uses refs for current indices to avoid stale React state when multiple commands are issued quickly. Reason: repeated “next/previous” commands were ignored after the first due to stale closures.
- **Prompt config**: Added `prompts.voiceMode` in `config.yaml` and use it for the voice mode system prompt. Reason: make prompt adjustable without code changes and tighten command-only tool usage.
- **UI behavior**: Voice mode no longer auto-opens the left panel (Q&A tab) when speaking/answering. Reason: keep voice mode hands-free and avoid unexpected UI changes.
