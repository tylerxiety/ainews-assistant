
# Fixes Plan: Stability & Performance

## Phase 1: Backend Performance & Deployment
- [ ] **Fix Event Loop Blocking**: Offload `BeautifulSoup` parsing to a thread pool in `backend/processor.py`
- [ ] **Optimize HTTP Client**: Reuse `httpx.AsyncClient` instance in `backend/processor.py` instead of creating new connections per request
- [ ] **Fix Deployment Script**: Remove hardcoded `PROJECT_ID` in `backend/deploy.sh` and use environment variable

## Phase 2: Frontend Resilience
- [ ] **Audio Error Handling**: Add `onError` handler to Audio Player in `frontend/src/components/Player.jsx` to catch playback failures
- [ ] **Global Error Boundary**: Create `ErrorBoundary.jsx` and wrap the React application to prevent white-screen crashes
- [ ] **PWA Configuration**: Add `manifest.json` to `frontend/public/` for installability

## Phase 3: Validation
- [ ] Verify local playback handles errors gracefully
- [ ] Verify backend parsing no longer blocks (code inspection)
