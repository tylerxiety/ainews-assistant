# Peer Review Fixes Implementation Plan

**Overall Progress:** `100%`

## TLDR
Fix validated issues from peer review: inconsistent console logging, error message exposure, duplicate manifest, and model version inconsistency.

## Critical Decisions
- **Console logging approach:** Wrap all console.error calls in `import.meta.env.DEV` checks for consistency (not removing them entirely, as they're useful for debugging)
- **Error handling in API:** Return generic "Internal Server Error" message to clients while keeping full error logged server-side
- **Model versioning:** Use environment variable consistently across all deployment configurations
- **GCS public URLs:** Keep as-is for now (audio content is not sensitive; signed URLs add complexity without clear benefit)

## Tasks:

- [x] 🟥 **Step 1: Fix Frontend Console Logging**
  - [x] 🟥 `Player.jsx:126` - Wrap console.error in dev check
  - [x] 🟥 `Player.jsx:72` - Add dev-only logging to empty catch block
  - [x] 🟥 `ErrorBoundary.jsx:18` - Wrap console.error in dev check

- [x] 🟥 **Step 2: Fix Backend Error Exposure**
  - [x] 🟥 `main.py:108` - Return generic error message instead of `str(e)`
  - [x] 🟥 `main.py:136` - Return generic error message instead of `str(e)`

- [x] 🟥 **Step 3: Remove Duplicate Manifest**
  - [x] 🟥 Delete `frontend/public/manifest.json` (VitePWA generates it)

- [x] 🟥 **Step 4: Standardize Gemini Model Version**
  - [x] 🟥 `deploy.sh:14` - Change default from `gemini-2.0-flash-exp` to `gemini-3-pro-preview`
  - [x] 🟥 `deploy-backend.yml:58` - Change from `gemini-2.0-flash-exp` to `gemini-3-pro-preview`
