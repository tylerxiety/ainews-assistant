"""
FastAPI application for newsletter processing service.
Version: 1.0.1
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import UTC, datetime

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


async def _fetch_issue_context(issue_id: str) -> str:
    segments_resp = (
        processor.supabase.table("segments")
        .select("content_clean, content_raw")
        .eq("issue_id", issue_id)
        .order("order_index")
        .execute()
    )

    if not segments_resp.data:
        return ""

    return "\n".join(
        seg.get("content_clean") or seg.get("content_raw", "")
        for seg in segments_resp.data
    )


@app.websocket("/ws/voice/{issue_id}")
async def voice_mode_ws(websocket: WebSocket, issue_id: str):
    await websocket.accept()

    start_payload = None
    try:
        start_payload = await asyncio.wait_for(websocket.receive_text(), timeout=1.5)
    except TimeoutError:
        start_payload = None
    except Exception:
        return

    context_text = await _fetch_issue_context(issue_id)
    if not context_text:
        await websocket.send_text(
            json.dumps(
                {"type": "error", "message": "Newsletter content not found for issue."}
            )
        )
        await websocket.close()
        return

    voice_session = VoiceSession(issue_id, context_text)
    if start_payload:
        await voice_session._handle_client_text(start_payload, websocket)

    await asyncio.gather(
        voice_session.listen_to_client(websocket),
        voice_session.run(websocket),
    )


@app.post("/ask-audio")
async def ask_question_audio(
    audio: UploadFile = File(...),
    issue_id: str = Form(...)
):
    """
    Ask a question about the entire newsletter issue using audio input.
    The audio is transcribed and answered in a single Gemini call.
    """
    try:
        answer_text, audio_url, transcript = await processor.ask_with_audio(
            audio,
            issue_id
        )

        return {
            "answer": answer_text,
            "audio_url": audio_url,
            "transcript": transcript
        }
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


# Only register test endpoint in development
if os.getenv("ENVIRONMENT", "production") == "development":
    @app.post("/process-test")
    async def process_newsletter_test(request: ProcessRequest):
        """
        Test endpoint: Process only first 10 segments (legacy).

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
                    clean_text, issue_id, 0, segment["order_index"]
                )
                segment["audio_url"] = audio_url
                segment["audio_duration_ms"] = duration_ms

            # Store segments
            processor.supabase.table("segments").insert(segments_data).execute()

            # Mark as processed
            processor.supabase.table("issues").update(
                {"processed_at": datetime.now(UTC).isoformat()}
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
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.post("/process-test-groups")
    async def process_newsletter_test_groups(request: ProcessRequest, num_groups: int = 2):
        """
        Test endpoint: Process only first N topic groups (default 2).

        Uses the new topic grouping logic with batch audio generation.
        Only available in development environment.
        """
        import asyncio

        try:
            # Fetch and parse
            raw_content = await processor._fetch_newsletter(str(request.url))
            issue_data, segments_data = processor._parse_newsletter(raw_content, str(request.url))

            # Group segments
            groups = processor._group_segments(segments_data)
            logger.info(f"Total groups found: {len(groups)}")

            # Limit to first N groups
            groups = groups[:num_groups]
            # Re-index
            for i, g in enumerate(groups):
                g["order_index"] = i

            logger.info(f"Processing {len(groups)} groups")

            # Upsert issue
            issue_result = processor.supabase.table("issues").upsert(
                issue_data,
                on_conflict="url"
            ).execute()
            issue_id = issue_result.data[0]["id"]

            # Delete old groups and segments if reprocessing
            processor.supabase.table("topic_groups").delete().eq("issue_id", issue_id).execute()

            # Process each group
            semaphore = asyncio.Semaphore(processor.max_concurrent_segments)

            async def process_group(group):
                async with semaphore:
                    group["issue_id"] = issue_id

                    # Prepare texts for cleaning
                    texts_to_clean = []
                    if group["label"]:
                        texts_to_clean.append(group["label"])
                    for seg in group["segments"]:
                        texts_to_clean.append(seg["content_raw"])

                    # Batch clean texts
                    cleaned_texts = await processor._clean_texts_batch(texts_to_clean)

                    # Assign back and prepare for audio
                    final_audio_texts = []
                    idx_offset = 0

                    if group["label"]:
                        final_audio_texts.append(cleaned_texts[0])
                        idx_offset = 1

                    for i, seg in enumerate(group["segments"]):
                        clean = cleaned_texts[i + idx_offset]
                        seg["content_clean"] = clean
                        final_audio_texts.append(clean)

                    # Generate combined audio
                    combined_text = " ... ".join(final_audio_texts)
                    audio_url, duration_ms = await processor._generate_audio(
                        combined_text, issue_id, group["order_index"], 0
                    )

                    group["audio_url"] = audio_url
                    group["audio_duration_ms"] = duration_ms

                    return group

            # Execute
            tasks = [process_group(g) for g in groups]
            processed_groups = []

            for future in asyncio.as_completed(tasks):
                try:
                    p_group = await future
                    processed_groups.append(p_group)
                    logger.info(f"Processed group {p_group['order_index']}: {p_group['label'][:50]}...")
                except Exception as e:
                    logger.error(f"Failed to process group: {e}")

            processed_groups.sort(key=lambda x: x["order_index"])

            # Insert groups
            groups_payload = [{
                "issue_id": issue_id,
                "label": g["label"],
                "audio_url": g["audio_url"],
                "audio_duration_ms": g["audio_duration_ms"],
                "order_index": g["order_index"]
            } for g in processed_groups]

            total_segments = 0
            if groups_payload:
                groups_resp = processor.supabase.table("topic_groups").insert(groups_payload).execute()
                inserted_groups = groups_resp.data

                group_id_map = {g["order_index"]: g["id"] for g in inserted_groups}

                # Prepare and insert segments
                all_segments = []
                for g in processed_groups:
                    g_id = group_id_map.get(g["order_index"])
                    if g_id is None:
                        continue
                    for seg in g["segments"]:
                        seg["issue_id"] = issue_id
                        seg["topic_group_id"] = g_id
                        if "content_clean" not in seg:
                            seg["content_clean"] = seg["content_raw"]
                        all_segments.append(seg)

                if all_segments:
                    processor.supabase.table("segments").insert(all_segments).execute()
                    total_segments = len(all_segments)

            # Mark as processed
            processor.supabase.table("issues").update(
                {"processed_at": datetime.now(UTC).isoformat()}
            ).eq("id", issue_id).execute()

            return {
                "status": "completed",
                "issue_id": issue_id,
                "groups_processed": len(processed_groups),
                "segments_processed": total_segments,
                "groups_detail": [{"label": g["label"][:60], "segments": len(g["segments"])} for g in processed_groups],
                "message": f"Test processing complete (first {num_groups} topic groups)"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in process_test_groups: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e)) from None

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
