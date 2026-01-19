# Backend Testing Guide

## Prerequisites

Ensure your environment is set up:
```bash
cd /Users/tylerxie/airepo/ainews-assistant/backend
source .venv/bin/activate
```

---

## Test 1: Health Check (30 seconds)

**Start the server:**
```bash
uvicorn main:app --reload --port 8080
```

**In another terminal, test health:**
```bash
curl http://localhost:8080/
```

**Expected response:**
```json
{"status":"healthy","service":"newsletter-audio-processor"}
```

✅ **Pass:** If you see the JSON response
❌ **Fail:** If you get connection refused or errors

---

## Test 2: Process 10 Segments (2-3 minutes, ~$1-2)

**Recommended for testing!** This processes only the first 10 segments.

**Request:**
```bash
curl -X POST http://localhost:8080/process-test \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"}'
```

**Expected response (takes 2-3 minutes):**
```json
{
  "status": "completed",
  "issue_id": "some-uuid-here",
  "segments_processed": 10,
  "message": "Test processing complete (first 10 segments only)"
}
```

**What happens:**
- ✅ Fetches newsletter HTML
- ✅ Parses into segments
- ✅ Processes first 10 segments only
- ✅ Cleans text with Gemini 3 Pro
- ✅ Generates audio with TTS
- ✅ Uploads to GCS
- ✅ Stores in Supabase

**Cost:** ~$1-2 (10 segments × $0.10-0.20 each)
**Time:** 2-3 minutes

---

## Test 3: Verify in Supabase

1. Go to https://supabase.com/dashboard/project/akxytmuwjomxlneqzgic/editor
2. Click **"Table Editor"** in left sidebar
3. Check these tables:

### Issues Table
- Should see 1 row with the newsletter title
- `processed_at` should have a timestamp

### Segments Table
- Should see 10 rows
- Each should have:
  - `content_raw`: Original text
  - `content_clean`: Cleaned text
  - `audio_url`: GCS URL (starts with `https://storage.googleapis.com/`)
  - `audio_duration_ms`: Duration in milliseconds

### Test Audio Playback
Copy an `audio_url` from the segments table and paste it in your browser. You should hear the audio play!

---

## Test 4: Check Individual Issue Status

Get the `issue_id` from the previous response, then:

```bash
curl http://localhost:8080/issues/{issue_id}
```

Replace `{issue_id}` with the actual UUID.

**Expected response:**
```json
{
  "issue": {
    "id": "...",
    "title": "ChatGPT starts testing ads...",
    "url": "https://news.smol.ai/issues/...",
    "processed_at": "2026-01-20T..."
  },
  "segment_count": 10,
  "status": "completed"
}
```

---

## Test 5: Full Processing (⚠️ EXPENSIVE - DO NOT RUN YET!)

**⚠️ WARNING:** Only run this when you're ready for production testing!

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"}'
```

**This will:**
- Process **all 754 segments**
- Take **1-2 hours**
- Cost **$75-150+** in GCP fees
- Block the request until complete

**Use this only when:**
- You've tested with `/process-test` first
- You're ready to test the full pipeline
- You understand the costs

---

## Troubleshooting

### Server won't start
**Error:** `supabase_url is required`
**Fix:** Check `.env` file exists in backend/ folder

### GCP authentication errors
**Error:** `403 Permission denied`
**Fix:** Check `service-account-key.json` exists and path in `.env` is correct

### Gemini errors
**Error:** `404 Model not found`
**Fix:** Ensure using `gemini-3-pro-preview` with `global` region

### TTS errors
**Error:** `Voice not found`
**Fix:** Voice name should be `en-US-Chirp3-HD-Aoede`

---

## Quick Test Scripts

You can also use the Python test scripts:

```bash
# Test Supabase connection
python test_connection.py

# Test GCP services
python test_gcp_connection.py

# Test Gemini 3 Pro
python test_gemini3_pro.py

# Test full pipeline (first 3 segments)
python test_pipeline.py
```

---

## Recommended Testing Flow

1. ✅ **Health check** (30 sec)
2. ✅ **Process 10 segments** (2-3 min, $1-2)
3. ✅ **Verify in Supabase** (1 min)
4. ✅ **Test audio playback** (30 sec)
5. ⏸️ **Full processing** (when ready for prod)

Total time for steps 1-4: **~5 minutes**
Total cost for steps 1-4: **~$1-2**

---

## Need Help?

Check the logs in the terminal where uvicorn is running. Errors will show up there.

To stop the server: `Ctrl+C` in the terminal running uvicorn.
