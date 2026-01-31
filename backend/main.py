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
    segments_resp = await asyncio.to_thread(
        lambda: processor.supabase.table("segments")
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
    issue_id: str = Form(...),
    language: str = Form("en")
):
    """
    Ask a question about the entire newsletter issue using audio input.
    The audio is transcribed and answered in a single Gemini call.

    Args:
        audio: Audio file containing the question
        issue_id: UUID of the issue
        language: Language code for response (en or zh)
    """
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


@app.post("/backfill-chinese")
async def backfill_chinese(n_segments: int | None = None, strategy: str = "first"):
    """
    Backfill Chinese translations and audio for the latest issue.

    This endpoint finds the most recently processed issue and adds Chinese
    content (content_raw_zh, content_clean_zh, audio_url_zh, audio_duration_ms_zh)
    for segments that don't already have it. Also adds label_zh to topic_groups.

    Args:
        n_segments: Optional limit on number of segments to process (for testing)
        strategy: Selection strategy - "first" (default) or "shortest" (for showcase)

    Returns:
        dict: Backfill status with counts of processed segments
    """
    try:
        # 1. Find the latest processed issue
        issues_resp = processor.supabase.table("issues") \
            .select("id, title") \
            .not_.is_("processed_at", "null") \
            .order("processed_at", desc=True) \
            .limit(1) \
            .execute()

        if not issues_resp.data:
            raise HTTPException(status_code=404, detail="No processed issues found")

        issue_id = issues_resp.data[0]["id"]
        issue_title = issues_resp.data[0]["title"]
        logger.info(f"Backfilling Chinese for issue: {issue_title} ({issue_id})")

        # 2. Fetch segments that need Chinese content
        segments_resp = processor.supabase.table("segments") \
            .select("id, content_raw, content_clean, topic_group_id, order_index") \
            .eq("issue_id", issue_id) \
            .is_("content_raw_zh", "null") \
            .order("order_index") \
            .execute()

        segments = segments_resp.data
        if not segments:
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "message": "All segments already have Chinese content"
            }

        # Apply selection strategy and limit
        if strategy == "shortest":
            # Sort by content length (shortest first) - better for TTS reliability
            segments = sorted(segments, key=lambda s: len(s.get("content_raw", "")))
            logger.info("Using 'shortest' strategy - selecting shortest segments")

        if n_segments is not None:
            segments = segments[:n_segments]
            logger.info(f"Limited to {n_segments} segments ({strategy} strategy)")

        # 3. Fetch topic groups that need Chinese labels
        groups_resp = processor.supabase.table("topic_groups") \
            .select("id, label") \
            .eq("issue_id", issue_id) \
            .is_("label_zh", "null") \
            .execute()

        groups = {g["id"]: g["label"] for g in groups_resp.data}

        # 4. Batch translate content_raw
        content_raw_list = [s["content_raw"] for s in segments]
        translated_raw = await processor._translate_texts_batch(content_raw_list)

        # 5. Clean translated texts for TTS
        texts_to_clean = [t for t in translated_raw if t is not None]
        if texts_to_clean:
            cleaned_zh = await processor._clean_texts_batch(texts_to_clean)
            cleaned_zh_iter = iter(cleaned_zh)
            translated_clean = [
                next(cleaned_zh_iter) if t is not None else None
                for t in translated_raw
            ]
        else:
            translated_clean = [None] * len(translated_raw)

        # 6. Translate group labels
        unique_labels = list(set(groups.values()))
        if unique_labels:
            translated_labels = await processor._translate_texts_batch(unique_labels)
            label_map = dict(zip(unique_labels, translated_labels))
        else:
            label_map = {}

        # 7. Generate Chinese audio and update segments
        processed_count = 0
        failed_count = 0

        for i, seg in enumerate(segments):
            raw_zh = translated_raw[i]
            clean_zh = translated_clean[i]

            if not clean_zh:
                logger.warning(f"No Chinese translation for segment {seg['id']}")
                failed_count += 1
                continue

            # Calculate group_index from topic_group_id
            # We need to find the order_index of the group
            group_order = 0
            if seg.get("topic_group_id"):
                group_resp = processor.supabase.table("topic_groups") \
                    .select("order_index") \
                    .eq("id", seg["topic_group_id"]) \
                    .single() \
                    .execute()
                if group_resp.data:
                    group_order = group_resp.data["order_index"]

            # Generate Chinese audio
            try:
                audio_url_zh, duration_ms_zh = await processor._generate_audio(
                    clean_zh, issue_id, group_order, seg["order_index"], language="zh"
                )
            except Exception as e:
                logger.error(f"Failed to generate Chinese audio for segment {seg['id']}: {e}")
                failed_count += 1
                continue

            # Update segment in database
            processor.supabase.table("segments").update({
                "content_raw_zh": raw_zh,
                "content_clean_zh": clean_zh,
                "audio_url_zh": audio_url_zh,
                "audio_duration_ms_zh": duration_ms_zh
            }).eq("id", seg["id"]).execute()

            processed_count += 1
            logger.info(f"Backfilled segment {processed_count}/{len(segments)}")

        # 8. Update topic groups with Chinese labels
        groups_updated = 0
        for group_id, label in groups.items():
            label_zh = label_map.get(label)
            if label_zh:
                processor.supabase.table("topic_groups").update({
                    "label_zh": label_zh
                }).eq("id", group_id).execute()
                groups_updated += 1

        return {
            "status": "completed",
            "issue_id": issue_id,
            "issue_title": issue_title,
            "segments_processed": processed_count,
            "segments_failed": failed_count,
            "groups_updated": groups_updated,
            "message": f"Backfilled Chinese content for {processed_count} segments"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backfill_chinese: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from None


@app.post("/backfill-section-headers")
async def backfill_section_headers(issue_id: str | None = None):
    """
    Backfill section headers for existing newsletters.

    This endpoint re-parses the newsletter HTML to identify section headers
    (like "AI Twitter Recap", "AI Reddit Recap") and inserts them as topic_groups
    with is_section_header=true.

    Args:
        issue_id: Optional specific issue to backfill. If not provided, processes the latest issue.

    Returns:
        dict: Backfill status with counts of section headers added
    """
    try:
        # Find the issue to backfill
        if issue_id:
            issues_resp = processor.supabase.table("issues") \
                .select("id, title, url") \
                .eq("id", issue_id) \
                .single() \
                .execute()
            if not issues_resp.data:
                raise HTTPException(status_code=404, detail="Issue not found")
            issue = issues_resp.data
        else:
            issues_resp = processor.supabase.table("issues") \
                .select("id, title, url") \
                .not_.is_("processed_at", "null") \
                .order("processed_at", desc=True) \
                .limit(1) \
                .execute()
            if not issues_resp.data:
                raise HTTPException(status_code=404, detail="No processed issues found")
            issue = issues_resp.data[0]

        issue_id = issue["id"]
        issue_url = issue["url"]
        logger.info(f"Backfilling section headers for issue: {issue['title']} ({issue_id})")

        # Fetch and re-parse the newsletter
        raw_content = await processor._fetch_newsletter(issue_url)
        _, segments_data = processor._parse_newsletter(raw_content, issue_url)

        # Group segments to identify section headers
        groups = processor._group_segments(segments_data)

        # Find section headers
        section_headers = [g for g in groups if g.get("is_section_header")]
        if not section_headers:
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "message": "No section headers found in this newsletter"
            }

        # Get existing groups to find insertion points
        existing_groups_resp = processor.supabase.table("topic_groups") \
            .select("id, label, order_index") \
            .eq("issue_id", issue_id) \
            .order("order_index") \
            .execute()

        existing_groups = existing_groups_resp.data
        if not existing_groups:
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "message": "No existing groups found for this issue"
            }

        # Build a map of label -> existing group for matching
        existing_by_label = {g["label"]: g for g in existing_groups}

        # For each section header, find where it should be inserted
        # by looking at the topic that follows it in the parsed data
        headers_added = 0
        for sh in section_headers:
            sh_label = sh["label"]
            sh_order = sh["order_index"]

            # Check if this section header already exists
            if sh_label in existing_by_label:
                logger.info(f"Section header '{sh_label}' already exists, skipping")
                continue

            # Find the next non-section-header group in parsed data
            next_topic = None
            for g in groups:
                if g["order_index"] > sh_order and not g.get("is_section_header"):
                    next_topic = g
                    break

            if next_topic and next_topic["label"] in existing_by_label:
                # Insert before this topic
                insert_before_order = existing_by_label[next_topic["label"]]["order_index"]
            else:
                # Insert at the end
                insert_before_order = max(g["order_index"] for g in existing_groups) + 1

            # Shift existing groups to make room
            processor.supabase.rpc(
                "increment_order_index",
                {"p_issue_id": issue_id, "p_min_order": insert_before_order}
            ).execute()

            # Generate audio for section header
            cleaned_labels = await processor._clean_texts_batch([sh_label])
            translated_labels = await processor._translate_texts_batch([sh_label])
            label_text_en = cleaned_labels[0] if cleaned_labels else sh_label
            label_zh = translated_labels[0] if translated_labels else None

            # Clean translated label for TTS
            label_text_zh = None
            if label_zh:
                cleaned_zh = await processor._clean_texts_batch([label_zh])
                label_text_zh = cleaned_zh[0] if cleaned_zh else None

            # Generate English audio
            audio_url, duration_ms = await processor._generate_audio(
                label_text_en, issue_id, insert_before_order, 0, language="en"
            )

            # Generate Chinese audio
            audio_url_zh, duration_ms_zh = None, None
            if label_text_zh:
                try:
                    audio_url_zh, duration_ms_zh = await processor._generate_audio(
                        label_text_zh, issue_id, insert_before_order, 0, language="zh"
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate Chinese audio for section header: {e}")

            # Insert section header
            processor.supabase.table("topic_groups").insert({
                "issue_id": issue_id,
                "label": sh_label,
                "label_zh": label_zh,
                "audio_url": audio_url,
                "audio_duration_ms": duration_ms,
                "audio_url_zh": audio_url_zh,
                "audio_duration_ms_zh": duration_ms_zh,
                "order_index": insert_before_order,
                "is_section_header": True
            }).execute()

            headers_added += 1
            logger.info(f"Added section header: {sh_label}")

            # Refresh existing groups map
            existing_groups_resp = processor.supabase.table("topic_groups") \
                .select("id, label, order_index") \
                .eq("issue_id", issue_id) \
                .order("order_index") \
                .execute()
            existing_by_label = {g["label"]: g for g in existing_groups_resp.data}

        return {
            "status": "completed",
            "issue_id": issue_id,
            "issue_title": issue["title"],
            "section_headers_added": headers_added,
            "message": f"Added {headers_added} section headers"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backfill_section_headers: {str(e)}", exc_info=True)
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
