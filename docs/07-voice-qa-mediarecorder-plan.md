# Voice Q&A: MediaRecorder + Server-Side Transcription

**Overall Progress:** `100%`

## TLDR

Replace browser Web Speech API with MediaRecorder API + server-side Gemini transcription for consistent voice Q&A across all platforms (iOS Safari/Chrome currently fail with garbled text).

## Critical Decisions

- **30s recording limit** - Prevent excessively long recordings
- **Tap-to-stop (manual)** - User taps mic to start, taps again to stop (simpler than silence detection)
- **Voice-only** - No text input fallback (cleaner UX)
- **Single Gemini call** - Transcribe + answer in one request for efficiency
- **New `/ask-audio` endpoint** - Separate from `/ask` for clean separation
- **Use existing Gemini 3 Pro Preview** - Same model as text processing (no new quota needed)
- **GCS-based audio upload** - Upload to GCS temporarily, use `Part.from_uri()` with Vertex AI SDK

## Tasks

- [x] 🟩 **Step 1: Create `useAudioRecorder` hook**
  - [x] 🟩 Create `frontend/src/hooks/useAudioRecorder.ts`
  - [x] 🟩 Use MediaRecorder API to record audio
  - [x] 🟩 Auto-detect format: `audio/webm;codecs=opus` (Chrome) or `audio/mp4` (Safari/iOS)
  - [x] 🟩 Expose: `isRecording`, `startRecording()`, `stopRecording()`, `audioBlob`, `error`
  - [x] 🟩 Enforce 30s max recording duration (auto-stop)

- [x] 🟩 **Step 2: Update Player.tsx**
  - [x] 🟩 Replace `useSpeechRecognition` import with `useAudioRecorder`
  - [x] 🟩 Update `handleMicClick`: tap to start recording, tap again to stop
  - [x] 🟩 On stop: send audio blob via `FormData` to `/ask-audio`
  - [x] 🟩 Update UI text: "Recording..." instead of "Listening..."
  - [x] 🟩 Remove `transcript` display during recording (server handles transcription)

- [x] 🟩 **Step 3: Add `/ask-audio` backend endpoint**
  - [x] 🟩 Add endpoint to `backend/main.py` accepting `multipart/form-data`
  - [x] 🟩 Accept: `audio` (UploadFile), `issue_id` (str), `group_id` (str)
  - [x] 🟩 Return: `{ answer, audio_url, transcript }` (enhanced format)

- [x] 🟩 **Step 4: Add `ask_with_audio()` method**
  - [x] 🟩 Import `Part` from `vertexai.generative_models` (already have `vertexai` SDK)
  - [x] 🟩 Use existing `self.gemini_model` (Gemini 3 Pro Preview) for audio processing
  - [x] 🟩 Implement `ask_with_audio()` in `backend/processor.py`:
    1. Upload audio to GCS temporarily (get `gs://` URI)
    2. Create `Part.from_uri()` with GCS URI and MIME type
    3. Call `gemini_model.generate_content([audio_part, prompt])` (single call: transcribe + answer)
    4. Parse response for transcript and answer
    5. Generate TTS for response
    6. Clean up temp audio from GCS
    7. Return answer text + audio URL + transcript

- [x] 🟩 **Step 5: Cleanup**
  - [x] 🟩 Delete `frontend/src/hooks/useSpeechRecognition.ts` (already deleted)
  - [x] 🟩 Remove `hasRecognitionSupport` check from Player.tsx (always show mic)

## Implementation Notes

**Secure Context Requirement:**
- MediaRecorder API requires HTTPS or localhost for security
- Works on `http://localhost:5173` ✅
- Fails on `http://192.168.x.x:5173` ❌
- Added feature detection with helpful error message
- For testing on mobile/other devices: use HTTPS tunnel (ngrok/localtunnel) or deploy to production with HTTPS

**Model & SDK:**
- Uses existing `vertexai` SDK (already in dependencies)
- Uses same Gemini 3 Pro Preview model as text processing
- No new dependencies or quota needed
- Audio uploaded to GCS temporarily, accessed via `Part.from_uri()` with `gs://` URI
