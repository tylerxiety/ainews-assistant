# Newsletter Audio Player - Implementation Plan

**Overall Progress:** `100%` (23/23 steps complete)

## TLDR
Build a PWA that converts AINews newsletter into listenable audio with clean TTS (no raw URLs/mentions read aloud), visual sync (auto-scroll + highlight), and tap-to-bookmark to ClickUp. Target: single-user MVP with end-to-end pipeline working.

## Production URLs
| Service | URL |
|---------|-----|
| **Frontend PWA** | https://ainews-assistant.vercel.app |
| **Backend API** | https://newsletter-processor-PROJECT_NUMBER.us-central1.run.app |
| **API Docs** | https://newsletter-processor-PROJECT_NUMBER.us-central1.run.app/docs |

## Current Status (2026-01-20)
✅ **Backend fully functional & deployed to Cloud Run**:
- Newsletter fetching & parsing (754 segments from AINews)
- Gemini 3 Pro text cleaning (@mentions, /r/ subreddits, links)
- TTS audio generation (Chirp 3 HD Aoede voice)
- GCS storage (public MP3 files)
- Supabase database (issues, segments, audio URLs)
- FastAPI endpoints (`/process`, `/process-test`, `/issues/{id}`)

✅ **Frontend PWA deployed to Vercel**:
- Supabase client setup with helper functions
- Issue List view showing all newsletters
- Player view with segment display
- Audio controls (play/pause, progress bar, speed selector)
- PWA installable on mobile with app icons
- Loading spinners and error states
- Responsive CSS for mobile

✅ **Phase 7 Complete** - PWA Features:
- vite-plugin-pwa configured with service worker
- App manifest with proper metadata
- App icons (192x192, 512x512 SVG)
- Install prompt banner
- Mobile-optimized viewport

✅ **Phase 8 Complete** - Deployment:
- Backend deployed to Cloud Run (us-central1)
- Frontend deployed to Vercel with environment variables
- Production URLs working end-to-end

✅ **Phase 6 Complete** - ClickUp Integration:
- Settings page with API token and List ID storage
- Bookmark button in player
- ClickUp task creation API integration
- Supabase bookmark storage

🎯 **Next**: Complete documentation (Phase 9, Step 23)

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
  - [x] 🟩 Reuse existing GCP project
  - [x] 🟩 Enable TTS, Storage, Vertex AI, Cloud Run APIs
  - [x] 🟩 Create GCS bucket
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

### Phase 3: Frontend - Basic UI ✅ COMPLETE

- [x] 🟩 **Step 9: Supabase Client Setup**
  - [x] 🟩 Create src/lib/supabase.js with client initialization
  - [x] 🟩 Add helper functions for fetching issues and segments
  - [x] 🟩 Test connection from frontend

- [x] 🟩 **Step 10: Issue List View**
  - [x] 🟩 Create IssueList component
  - [x] 🟩 Fetch all issues from Supabase
  - [x] 🟩 Display title, published date, processing status
  - [x] 🟩 Add click handler to navigate to player view
  - [x] 🟩 Style with plain CSS

- [x] 🟩 **Step 11: Player View - Basic**
  - [x] 🟩 Create Player component
  - [x] 🟩 Fetch issue + segments for selected issue
  - [x] 🟩 Render segment content (content_raw)
  - [x] 🟩 Display segments in order
  - [x] 🟩 Style with plain CSS

- [x] 🟩 **Step 12: Audio Player Controls**
  - [x] 🟩 Add HTML5 audio element
  - [x] 🟩 Create playlist from segment audio URLs
  - [x] 🟩 Implement play/pause controls
  - [x] 🟩 Add playback speed selector (1x, 1.25x, 1.5x, 2x)
  - [x] 🟩 Add progress bar
  - [x] 🟩 Style controls

### Phase 4: First Milestone - End-to-End Test ✅ COMPLETE

- [x] 🟩 **Step 13: Smoke Test**
  - [x] 🟩 Start backend locally
  - [x] 🟩 Verify segments appear in Supabase
  - [x] 🟩 Verify audio files in GCS
  - [x] 🟩 Start frontend locally
  - [x] 🟩 Navigate to issue list, see processed issue
  - [x] 🟩 Click issue, hear audio play
  - [x] 🟩 Document any issues/fixes needed

### Phase 5: Audio Sync & Highlighting ✅ COMPLETE

- [x] 🟩 **Step 14: Audio Sync Implementation**
  - [x] 🟩 Calculate cumulative start times for each segment (via segment index tracking)
  - [x] 🟩 Add timeupdate event listener to audio element
  - [x] 🟩 Determine current segment based on playback time
  - [x] 🟩 Highlight current segment (CSS class)
  - [x] 🟩 Auto-scroll to current segment (scrollIntoView)

- [x] 🟩 **Step 15: Sync Polish**
  - [x] 🟩 Add smooth scroll behavior
  - [x] 🟩 Ensure highlight updates in real-time
  - [x] 🟩 Test with various playback speeds
  - [x] 🟩 Handle edge cases (first/last segment)

### Phase 6: ClickUp Integration ✅ COMPLETE

- [x] 🟩 **Step 16: Settings Page**
  - [x] 🟩 Create Settings component
  - [x] 🟩 Add input for ClickUp API token
  - [x] 🟩 Add input for ClickUp list ID
  - [x] 🟩 Store in localStorage
  - [x] 🟩 Style settings page

- [x] 🟩 **Step 17: Bookmark Functionality**
  - [x] 🟩 Add bookmark button to each segment
  - [x] 🟩 Implement ClickUp API call (POST to /list/{id}/task)
  - [x] 🟩 Create task with segment content + first link as description
  - [x] 🟩 Store bookmark in Supabase bookmarks table
  - [x] 🟩 Show visual indicator for bookmarked items
  - [x] 🟩 Add error handling for API failures

### Phase 7: PWA Features ✅ COMPLETE

- [x] 🟩 **Step 18: PWA Configuration**
  - [x] 🟩 Configure vite-plugin-pwa in vite.config.js
  - [x] 🟩 Create manifest.webmanifest with app metadata
  - [x] 🟩 Add app icons (192x192, 512x512 SVG)
  - [x] 🟩 Configure service worker for offline support
  - [x] 🟩 Test installation on mobile

- [x] 🟩 **Step 19: PWA Polish**
  - [x] 🟩 Add install prompt banner
  - [x] 🟩 Test offline behavior
  - [x] 🟩 Add loading states
  - [x] 🟩 Optimize for mobile viewport

### Phase 8: Deployment ✅ COMPLETE

- [x] 🟩 **Step 20: Backend Deployment**
  - [x] 🟩 Build Docker image via Cloud Build
  - [x] 🟩 Deploy to Cloud Run (newsletter-processor)
  - [x] 🟩 Configure environment variables in Cloud Run
  - [x] 🟩 Test deployed endpoint
  - [x] 🟩 Set up Cloud Scheduler (every 6 hours, `newsletter-processor-trigger`)

- [x] 🟩 **Step 21: Frontend Deployment**
  - [x] 🟩 Configure Vercel project (ainews-assistant)
  - [x] 🟩 Set environment variables in Vercel (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL)
  - [x] 🟩 Deploy frontend (https://ainews-assistant.vercel.app)
  - [x] 🟩 CORS already configured for all origins
  - [x] 🟩 Test production deployment end-to-end

### Phase 9: Polish & Documentation ⏳ IN PROGRESS

- [x] 🟩 **Step 22: Final Polish**
  - [x] 🟩 Add loading spinners for async operations
  - [x] 🟩 Add error messages for failed operations
  - [x] 🟩 Improve CSS styling (responsive, accessible)
  - [x] 🟩 Test on different devices/browsers
  - [x] 🟩 Fix any bugs discovered

- [x] 🟩 **Step 23: Documentation**
  - [x] 🟩 Update README with deployment URLs
  - [x] 🟩 Document any gotchas or manual steps
  - [x] 🟩 Create user guide for ClickUp setup

## Out of Scope for MVP
- Voice commands
- Interrupt-to-ask features

## Success Criteria
- ✅ **Can process one newsletter issue automatically** - Working! (13 segments processed)
- ✅ **Audio plays in browser with clean, natural TTS** - Working! (Chirp 3 HD Aoede)
- ✅ **Visual sync highlights current segment during playback** - Working! (auto-scroll + highlight)
- ✅ **Can bookmark items to ClickUp with one tap** - Working! (Settings + API integration)
- ✅ **Works as installable PWA on mobile** - Working! (install banner, app icons)
- ✅ **Deployed to production (Vercel + Cloud Run)** - Working! (see Production URLs above)
