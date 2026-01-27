# Centralized Configuration Implementation Plan

**Overall Progress:** `100%`

## TLDR
Create a single YAML configuration file at project root (`/config.yaml`) containing all frontend config, backend config, and prompts. This enables easy experimentation with different Gemini models and prompt tuning from one place. Frontend loads via Vite YAML plugin, backend loads via PyYAML.

## Critical Decisions
- **Single YAML file at root** - `/config.yaml` for all non-secret settings, easy to find everything
- **Vite YAML plugin** - `@rollup/plugin-yaml` for clean frontend imports
- **Secrets stay in `.env`** - Supabase keys, GCP credentials remain environment variables
- **Prompts in YAML** - Clean multiline strings, easy to edit and experiment with
- **Remove dead `/ask` endpoint** - Legacy code from browser-native STT, no longer used

## Tasks:

- [x] 🟩 **Step 1: Create `/config.yaml`**
  - [x] 🟩 Create YAML file with `frontend`, `backend`, and `prompts` sections
  - [x] 🟩 Add clear section comments

- [x] 🟩 **Step 2: Setup Frontend YAML Loading**
  - [x] 🟩 Install `@rollup/plugin-yaml`
  - [x] 🟩 Configure `vite.config.ts` to use YAML plugin
  - [x] 🟩 Add TypeScript declaration for `.yaml` imports

- [x] 🟩 **Step 3: Update `frontend/src/config.ts`**
  - [x] 🟩 Import from `../../config.yaml`
  - [x] 🟩 Export typed CONFIG object for frontend use

- [x] 🟩 **Step 4: Setup Backend YAML Loading**
  - [x] 🟩 Add `pyyaml` to `pyproject.toml`
  - [x] 🟩 Update `backend/config.py` to load from YAML + merge `.env` secrets

- [x] 🟩 **Step 5: Refactor `processor.py`**
  - [x] 🟩 Use Config for model names, TTS settings, processing params
  - [x] 🟩 Use prompts from Config instead of inline strings
  - [x] 🟩 Create separate Gemini model instances for cleaning vs Q&A

- [x] 🟩 **Step 6: Refactor `main.py`**
  - [x] 🟩 Use Config for processor initialization

- [x] 🟩 **Step 7: Remove Dead Code**
  - [x] 🟩 Remove `AskRequest` class from `main.py`
  - [x] 🟩 Remove `/ask` endpoint from `main.py`
  - [x] 🟩 Remove `ask()` method from `processor.py`

- [x] 🟩 **Step 8: Update Frontend Components**
  - [x] 🟩 Update `Player.tsx` to use new config path
  - [x] 🟩 Update `useAudioRecorder.ts` to import from config

## Testing (Required)

### Approach
API (curl) + browser-based testing

### Test Scenarios
- [x] 🟩 Frontend build: `npm run build` completes without errors
- [x] 🟩 Backend startup: Config loads from YAML correctly
- [x] 🟩 Config values verified: Models, TTS, prompts all loaded
- [x] 🟩 `/ask` endpoint removed: Returns 404 (verified via route inspection)
- [x] 🟩 Q&A flow: Browser test confirmed player loads with mic button visible

### Acceptance Criteria
- [x] Single `/config.yaml` file contains all non-secret settings
- [x] Frontend imports config without errors
- [x] Backend loads config and uses correct model names
- [x] Prompts in YAML are used correctly (verified via backend logs)
- [x] `/ask` endpoint removed
- [x] Q&A audio flow works end-to-end (user tested, browser verified)

---

## Reference: YAML Structure

```yaml
# /config.yaml

# =============================================================================
# FRONTEND
# =============================================================================
frontend:
  qa:
    resumeDelayMs: 1500
    maxRecordingDurationMs: 30000

# =============================================================================
# BACKEND
# =============================================================================
backend:
  processing:
    maxConcurrentSegments: 5
    httpTimeoutSeconds: 30.0
    segmentBatchSize: 50
  
  ai:
    models:
      textCleaning: "gemini-3-pro-preview"
      qa: "gemini-3-pro-preview"
  
  tts:
    voiceName: "en-US-Chirp3-HD-Aoede"
    languageCode: "en-US"
    speakingRate: 1.0

# =============================================================================
# PROMPTS
# =============================================================================
prompts:
  textCleaning: |
    Clean the following list of newsletter texts for text-to-speech.
    Return a JSON array of strings...
    
  qaWithAudio: |
    You are an AI assistant helping a user listen to a newsletter...
```
