"""
FastAPI application for newsletter processing service.
Version: 1.0.1
"""
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import os
from typing import Optional
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from processor import NewsletterProcessor

app = FastAPI(title="Newsletter Audio Processor")

# Logger will be configured at startup
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    """Configure logging on startup to avoid conflicts with Uvicorn."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info("Newsletter Audio Processor starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await processor.close()
    logger.info("Newsletter Audio Processor shutting down")

# CORS middleware for frontend access
# In production, set ALLOWED_ORIGINS env var (comma-separated)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor
processor = NewsletterProcessor(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY"),
    gcp_project_id=os.getenv("GCP_PROJECT_ID"),
    gcp_region=os.getenv("GCP_REGION"),
    gcs_bucket_name=os.getenv("GCS_BUCKET_NAME"),
    gemini_model_name=os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
    max_concurrent_segments=int(os.getenv("MAX_CONCURRENT_SEGMENTS", "5")),
    tts_voice_name=os.getenv("TTS_VOICE_NAME", "en-US-Chirp3-HD-Aoede"),
)


class ProcessRequest(BaseModel):
    url: HttpUrl


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "newsletter-audio-processor"}


@app.post("/process")
async def process_newsletter(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Process a newsletter issue: fetch, parse, clean text, generate audio.
    Processing happens in the background to avoid request timeouts.

    Args:
        request: ProcessRequest with newsletter URL
        background_tasks: FastAPI BackgroundTasks

    Returns:
        dict: Processing status and issue_id
    """
    try:
        # Generate issue ID upfront
        issue_id = str(uuid.uuid4())

        # Process newsletter in background to avoid timeouts
        background_tasks.add_task(
            processor.process_newsletter,
            str(request.url),
            issue_id
        )

        return {
            "status": "processing",
            "issue_id": issue_id,
            "message": "Newsletter processing started in background"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/issues/{issue_id}")
async def get_issue_status(issue_id: str):
    """
    Get processing status for a specific issue.

    Args:
        issue_id: UUID of the issue

    Returns:
        dict: Issue processing status and details
    """
    # Validate UUID format before querying database
    try:
        uuid.UUID(issue_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid issue_id format")

    try:
        status = await processor.get_issue_status(issue_id)
        if not status:
            raise HTTPException(status_code=404, detail="Issue not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Only register test endpoint in development
if os.getenv("ENVIRONMENT", "development") == "development":
    @app.post("/process-test")
    async def process_newsletter_test(request: ProcessRequest):
        """
        Test endpoint: Process only first 10 segments.

        Use this for testing without high costs.
        Only available in development environment.
        """
        try:
            # Fetch and parse
            raw_content = await processor._fetch_newsletter(str(request.url))
            issue_data, segments_data = processor._parse_newsletter(raw_content, str(request.url))

            # Limit to first 10 segments
            segments_data = segments_data[:10]

            # Upsert issue to handle race conditions
            issue_result = processor.supabase.table("issues").upsert(
                issue_data,
                on_conflict="url"
            ).execute()
            issue_id = issue_result.data[0]["id"]

            # Delete old segments if reprocessing
            processor.supabase.table("segments").delete().eq("issue_id", issue_id).execute()

            # Process segments
            for segment in segments_data:
                segment["issue_id"] = issue_id
                clean_text = await processor._clean_text_for_tts(segment["content_raw"])
                segment["content_clean"] = clean_text

                audio_url, duration_ms = await processor._generate_audio(
                    clean_text, issue_id, segment["order_index"]
                )
                segment["audio_url"] = audio_url
                segment["audio_duration_ms"] = duration_ms

            # Store segments
            processor.supabase.table("segments").insert(segments_data).execute()

            # Mark as processed
            processor.supabase.table("issues").update(
                {"processed_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", issue_id).execute()

            return {
                "status": "completed",
                "issue_id": issue_id,
                "segments_processed": len(segments_data),
                "message": "Test processing complete (first 10 segments only)"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
