# Newsletter Audio Player - Implementation Plan

**Overall Progress:** `35%` (8/23 steps complete)

## TLDR
Build a PWA that converts AINews newsletter into listenable audio with clean TTS (no raw URLs/mentions read aloud), visual sync (auto-scroll + highlight), and tap-to-bookmark to ClickUp. Target: single-user MVP with end-to-end pipeline working.

## Current Status (2026-01-20)
✅ **Backend fully functional** - Complete processing pipeline working:
- Newsletter fetching & parsing (754 segments from AINews)
- Gemini 3 Pro text cleaning (@mentions, /r/ subreddits, links)
- TTS audio generation (Chirp 3 HD Aoede voice)
- GCS storage (public MP3 files)
- Supabase database (issues, segments, audio URLs)
- FastAPI endpoints (`/process`, `/process-test`, `/issues/{id}`)
- 13 segments successfully processed with working audio playback

🚧 **In Progress**: Phase 4 - First Milestone (partial)
- Backend smoke test passed
- Frontend UI not yet built

🎯 **Next**: Build frontend React UI to complete end-to-end smoke test

## Critical Decisions
- **TTS Engine**: Google Cloud TTS Chirp 3 HD Aoede (en-US female voice) - High quality, natural-sounding
- **Text Cleaning**: Gemini 3 Pro Preview (global region) - Handles @mentions, /r/ subreddits, markdown links naturally
- **Audio Strategy**: Per-segment audio files for fine-grained sync, client-side concatenation/playlist
- **Database**: Supabase Postgres - Real-time subscriptions for live updates
- **Deployment**: Vercel (frontend) + Cloud Run (backend) - Serverless, auto-scaling
- **Auth**: None for MVP (single user, personal tool)
- **Python Environment**: Python 3.12+ with uv package manager for fast dependency management

## Tasks:

### Phase 1: Infrastructure & Setup ✅ COMPLETE

- [x] 🟩 **Step 1: Scaffold Monorepo Structure**
  - [x] 🟩 Create frontend/ with Vite + React
  - [x] 🟩 Create backend/ with Python structure
  - [x] 🟩 Create supabase/migrations/ folder
  - [x] 🟩 Install frontend dependencies (Supabase client, PWA plugin)
  - [x] 🟩 Create requirements.txt with all backend dependencies

- [x] 🟩 **Step 2: Database Setup**
  - [x] 🟩 Create Supabase project (akxytmuwjomxlneqzgic)
  - [x] 🟩 Run initial migration (001_initial_schema.sql)
  - [x] 🟩 Verify tables created (issues, segments, bookmarks)
  - [x] 🟩 Get Supabase URL and keys

- [x] 🟩 **Step 3: GCP Setup**
  - [x] 🟩 Reuse existing GCP project (gen-lang-client-0104465868/heidi)
  - [x] 🟩 Enable TTS, Storage, Vertex AI, Cloud Run APIs
  - [x] 🟩 Create GCS bucket (ainews-assistant-audio-heidi)
  - [x] 🟩 Create service account (ainews-processor) with proper permissions
  - [x] 🟩 Download service account key JSON

- [x] 🟩 **Step 4: Environment Configuration**
  - [x] 🟩 Configure backend .env with Supabase + GCP credentials
  - [x] 🟩 Configure frontend .env.local with Supabase credentials
  - [x] 🟩 Test backend connection to Supabase
  - [x] 🟩 Test GCP authentication (TTS, Storage, Gemini all working)

### Phase 2: Backend Processing Pipeline ✅ COMPLETE

- [x] 🟩 **Step 5: RSS Feed Parsing**
  - [x] 🟩 Implement fetch_newsletter() to get HTML from URL
  - [x] 🟩 Enhance parse_newsletter() for AINews HTML structure
  - [x] 🟩 Extract issue title and published date
  - [x] 🟩 Parse sections (h1/h2/h3 headers) and items (list items)
  - [x] 🟩 Extract links from each item into JSONB format

- [x] 🟩 **Step 6: Text Cleaning with Gemini**
  - [x] 🟩 Implement Gemini 3 Pro Preview API call in clean_text_for_tts()
  - [x] 🟩 Add transformation rules (@username, /r/subreddit, markdown links)
  - [x] 🟩 Add "Now:" prefix for section headers
  - [x] 🟩 Test with sample newsletter text (working!)

- [x] 🟩 **Step 7: Audio Generation with TTS**
  - [x] 🟩 Configure Chirp 3 HD Aoede voice in generate_audio()
  - [x] 🟩 Implement text-to-speech synthesis
  - [x] 🟩 Upload audio to GCS with proper naming (issue_id/segment_N.mp3)
  - [x] 🟩 Store GCS public URLs in segments table
  - [x] 🟩 Make audio files publicly accessible

- [x] 🟩 **Step 8: Complete Processing Pipeline**
  - [x] 🟩 Wire up process_newsletter() full flow
  - [x] 🟩 Add error handling for duplicate issues
  - [x] 🟩 Update processed_at timestamp on completion
  - [x] 🟩 Test with real newsletter URL (13 segments processed successfully)

### Phase 3: Frontend - Basic UI (Current Phase)

- [ ] 🟥 **Step 9: Supabase Client Setup**
  - [ ] 🟥 Create src/lib/supabase.ts with client initialization
  - [ ] 🟥 Add helper functions for fetching issues and segments
  - [ ] 🟥 Test connection from frontend

- [ ] 🟥 **Step 10: Issue List View**
  - [ ] 🟥 Create IssueList component
  - [ ] 🟥 Fetch all issues from Supabase
  - [ ] 🟥 Display title, published date, processing status
  - [ ] 🟥 Add click handler to navigate to player view
  - [ ] 🟥 Style with plain CSS

- [ ] 🟥 **Step 11: Player View - Basic**
  - [ ] 🟥 Create Player component
  - [ ] 🟥 Fetch issue + segments for selected issue
  - [ ] 🟥 Render newsletter HTML content
  - [ ] 🟥 Display segments in order
  - [ ] 🟥 Style with plain CSS

- [ ] 🟥 **Step 12: Audio Player Controls**
  - [ ] 🟥 Add HTML5 audio element
  - [ ] 🟥 Create playlist from segment audio URLs
  - [ ] 🟥 Implement play/pause controls
  - [ ] 🟥 Add playback speed selector (1x, 1.25x, 1.5x, 2x)
  - [ ] 🟥 Add progress bar
  - [ ] 🟥 Style controls

### Phase 4: First Milestone - End-to-End Test

- [ ] 🟥 **Step 13: Smoke Test**
  - [ ] 🟥 Start backend locally
  - [ ] 🟥 Trigger /process with test newsletter URL
  - [ ] 🟥 Verify segments appear in Supabase
  - [ ] 🟥 Verify audio files in GCS
  - [ ] 🟥 Start frontend locally
  - [ ] 🟥 Navigate to issue list, see processed issue
  - [ ] 🟥 Click issue, hear audio play
  - [ ] 🟥 Document any issues/fixes needed

### Phase 5: Audio Sync & Highlighting

- [ ] 🟥 **Step 14: Audio Sync Implementation**
  - [ ] 🟥 Calculate cumulative start times for each segment
  - [ ] 🟥 Add timeupdate event listener to audio element
  - [ ] 🟥 Determine current segment based on playback time
  - [ ] 🟥 Highlight current segment (CSS class)
  - [ ] 🟥 Auto-scroll to current segment (scrollIntoView)

- [ ] 🟥 **Step 15: Sync Polish**
  - [ ] 🟥 Add smooth scroll behavior
  - [ ] 🟥 Ensure highlight updates in real-time
  - [ ] 🟥 Test with various playback speeds
  - [ ] 🟥 Handle edge cases (first/last segment)

### Phase 6: ClickUp Integration

- [ ] 🟥 **Step 16: Settings Page**
  - [ ] 🟥 Create Settings component
  - [ ] 🟥 Add input for ClickUp API token
  - [ ] 🟥 Add input for ClickUp list ID
  - [ ] 🟥 Store in localStorage
  - [ ] 🟥 Style settings page

- [ ] 🟥 **Step 17: Bookmark Functionality**
  - [ ] 🟥 Add bookmark button to each segment
  - [ ] 🟥 Implement ClickUp API call (POST to /list/{id}/task)
  - [ ] 🟥 Create task with segment content + first link as description
  - [ ] 🟥 Store bookmark in Supabase bookmarks table
  - [ ] 🟥 Show visual indicator for bookmarked items
  - [ ] 🟥 Add error handling for API failures

### Phase 7: PWA Features

- [ ] 🟥 **Step 18: PWA Configuration**
  - [ ] 🟥 Configure vite-plugin-pwa in vite.config.js
  - [ ] 🟥 Create manifest.json with app metadata
  - [ ] 🟥 Add app icons (192x192, 512x512)
  - [ ] 🟥 Configure service worker for offline support
  - [ ] 🟥 Test installation on mobile

- [ ] 🟥 **Step 19: PWA Polish**
  - [ ] 🟥 Add install prompt
  - [ ] 🟥 Test offline behavior
  - [ ] 🟥 Add loading states
  - [ ] 🟥 Optimize for mobile viewport

### Phase 8: Deployment

- [ ] 🟥 **Step 20: Backend Deployment**
  - [ ] 🟥 Build Docker image
  - [ ] 🟥 Deploy to Cloud Run
  - [ ] 🟥 Configure environment variables in Cloud Run
  - [ ] 🟥 Test deployed endpoint
  - [ ] 🟥 Set up Cloud Scheduler (every 6 hours, optional for MVP)

- [ ] 🟥 **Step 21: Frontend Deployment**
  - [ ] 🟥 Configure Vercel project
  - [ ] 🟥 Set environment variables in Vercel
  - [ ] 🟥 Deploy frontend
  - [ ] 🟥 Update CORS settings in backend for production domain
  - [ ] 🟥 Test production deployment end-to-end

### Phase 9: Polish & Documentation

- [ ] 🟥 **Step 22: Final Polish**
  - [ ] 🟥 Add loading spinners for async operations
  - [ ] 🟥 Add error messages for failed operations
  - [ ] 🟥 Improve CSS styling (responsive, accessible)
  - [ ] 🟥 Test on different devices/browsers
  - [ ] 🟥 Fix any bugs discovered

- [ ] 🟥 **Step 23: Documentation**
  - [ ] 🟥 Update README with deployment URLs
  - [ ] 🟥 Document any gotchas or manual steps
  - [ ] 🟥 Add screenshots to docs/
  - [ ] 🟥 Create user guide for ClickUp setup

## Out of Scope for MVP
- User authentication
- Multiple newsletters support
- Offline download of episodes
- Voice commands
- Interrupt-to-ask features
- Multi-user support
- Custom voice selection UI

## Success Criteria
- ✅ **Can process one newsletter issue automatically** - Working! (13 segments processed)
- ✅ **Audio plays in browser with clean, natural TTS** - Working! (Chirp 3 HD Aoede)
- ⏸️ Visual sync highlights current segment during playback - Pending frontend
- ⏸️ Can bookmark items to ClickUp with one tap - Pending frontend
- ⏸️ Works as installable PWA on mobile - Pending frontend + PWA config
- ⏸️ Deployed to production (Vercel + Cloud Run) - Pending deployment
