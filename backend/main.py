"""
FastAPI application for newsletter processing service.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import os
from typing import Optional

from processor import NewsletterProcessor

app = FastAPI(title="Newsletter Audio Processor")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
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

    Args:
        request: ProcessRequest with newsletter URL
        background_tasks: FastAPI background tasks

    Returns:
        dict: Processing status and issue_id
    """
    try:
        # Start processing in background
        issue_id = await processor.process_newsletter(str(request.url))

        return {
            "status": "processing",
            "issue_id": issue_id,
            "message": "Newsletter processing started"
        }
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
    try:
        status = await processor.get_issue_status(issue_id)
        if not status:
            raise HTTPException(status_code=404, detail="Issue not found")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
