"""
FastAPI application for newsletter processing service.
Version: 1.0.1
"""
import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

# Load environment variables
load_dotenv()

from processor import NewsletterProcessor
from voice_session import VoiceSession

# Logger will be configured at startup
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info("Newsletter Audio Processor starting up")
    yield
    await processor.close()
    logger.info("Newsletter Audio Processor shutting down")


app = FastAPI(title="Newsletter Audio Processor", lifespan=lifespan)

# CORS middleware for frontend access
from config import Config

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor with secrets from .env (config from config.yaml)
processor = NewsletterProcessor(
    supabase_url=Config.SUPABASE_URL,
    supabase_key=Config.SUPABASE_KEY,
    gcp_project_id=Config.GCP_PROJECT_ID,
    gcs_bucket_name=Config.GCS_BUCKET_NAME,
)


class ProcessRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "newsletter-audio-processor"}


async def _fetch_issue_context(issue_id: str, language: str = "en") -> str:
    # Select Chinese columns when language is zh
    if language == "zh":
        segments_resp = await asyncio.to_thread(
            lambda: processor.supabase.table("segments")
            .select("content_clean, content_raw, content_clean_zh, content_raw_zh")
            .eq("issue_id", issue_id)
            .order("order_index")
            .execute()
        )
    else:
        segments_resp = await asyncio.to_thread(
            lambda: processor.supabase.table("segments")
            .select("content_clean, content_raw")
            .eq("issue_id", issue_id)
            .order("order_index")
            .execute()
        )

    if not segments_resp.data:
        return ""

    # Use Chinese content if available, fallback to English
    if language == "zh":
        return "\n".join(
            seg.get("content_clean_zh") or seg.get("content_raw_zh") or seg.get("content_clean") or seg.get("content_raw", "")
            for seg in segments_resp.data
        )
    return "\n".join(
        seg.get("content_clean") or seg.get("content_raw", "")
        for seg in segments_resp.data
    )


@app.websocket("/ws/voice/{issue_id}")
async def voice_mode_ws(websocket: WebSocket, issue_id: str, language: Literal["en", "zh"] = "en"):
    # Validate UUID format before proceeding
    try:
        uuid.UUID(issue_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid issue_id format")
        return

    await websocket.accept()

    start_payload = None
    try:
        start_payload = await asyncio.wait_for(websocket.receive_text(), timeout=1.5)
    except TimeoutError:
        start_payload = None
    except Exception:
        return

    context_text = await _fetch_issue_context(issue_id, language)
    if not context_text:
        await websocket.send_text(
            json.dumps(
                {"type": "error", "message": "Newsletter content not found for issue."}
            )
        )
        await websocket.close()
        return

    voice_session = VoiceSession(issue_id, context_text, language=language)
    if start_payload:
        await voice_session.handle_client_text(start_payload, websocket)

    await asyncio.gather(
        voice_session.listen_to_client(websocket),
        voice_session.run(websocket),
    )


@app.post("/ask-audio")
async def ask_question_audio(
    audio: UploadFile = File(...),
    issue_id: str = Form(...),
    language: Literal["en", "zh"] = Form("en")
):
    """
    Ask a question about the entire newsletter issue using audio input.
    The audio is transcribed and answered in a single Gemini call.

    Args:
        audio: Audio file containing the question
        issue_id: UUID of the issue
        language: Language code for response (en or zh)
    """
    # Validate UUID format
    try:
        uuid.UUID(issue_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid issue_id format") from None

    try:
        answer_text, audio_url, transcript = await processor.ask_with_audio(
            audio,
            issue_id,
            language=language
        )

        return {
            "answer": answer_text,
            "audio_url": audio_url,
            "transcript": transcript
        }
    except ValueError as e:
        logger.warning(f"Bad request in ask_question_audio: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error in ask_question_audio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from None


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
        logger.error(f"Error processing newsletter: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from None


@app.post("/process-latest")
async def process_latest_newsletter(force: bool = False):
    """
    Discover and process the latest newsletter from RSS feed.
    
    This endpoint is designed to be called by Cloud Scheduler every 6 hours.
    It automatically:
    1. Fetches the RSS feed to find the latest newsletter URL
    2. Checks if this issue has already been processed
    3. If new, triggers processing synchronously (to ensure completion on Cloud Run)
    
    Args:
        force: If True, bypass the check for existing issue and re-process.

    Returns:
        dict: Processing status - 'skipped' if already processed, 
              'completed' if new issue found and processed, or 'no_new_issue' if RSS fetch failed
    """
    try:
        # Step 1: Discover latest newsletter URL from RSS
        latest_url = await processor.fetch_latest_newsletter_url()
        
        if not latest_url:
            logger.warning("No newsletter URL found in RSS feed")
            return {
                "status": "no_new_issue",
                "message": "Could not fetch latest newsletter URL from RSS feed"
            }
        
        # Step 2: Check if already processed
        if not force and processor.check_issue_exists(latest_url):
            logger.info(f"Newsletter already processed: {latest_url}")
            return {
                "status": "skipped",
                "url": latest_url,
                "message": "Newsletter already processed"
            }
        
        # Step 3: Process new newsletter synchronously
        issue_id = str(uuid.uuid4())
        logger.info(f"New newsletter found, starting processing: {latest_url}")
        
        # Wait for processing to complete
        await processor.process_newsletter(latest_url, issue_id)

        return {
            "status": "completed",
            "issue_id": issue_id,
            "url": latest_url,
            "message": "New newsletter found and processed successfully"
        }
    except Exception as e:
        logger.error(f"Error in process_latest_newsletter: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from None


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
        raise HTTPException(status_code=400, detail="Invalid issue_id format") from None

    try:
        status = await processor.get_issue_status(issue_id)
        if not status:
            raise HTTPException(status_code=404, detail="Issue not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching issue status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from None


# Serve Frontend (only if directory exists, for safety)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(frontend_dist):
    # Mount assets directly to handle MIME types correctly
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Check if file exists in dist (e.g. favicon.ico, manifest.json)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fallback to index.html for React Router
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
