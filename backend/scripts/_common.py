"""
Shared utilities for admin scripts.
"""
import logging
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")

from config import Config
from processor import NewsletterProcessor


def setup_logging() -> logging.Logger:
    """Configure logging for scripts."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def get_processor() -> NewsletterProcessor:
    """Create and return a configured NewsletterProcessor instance."""
    return NewsletterProcessor(
        supabase_url=Config.SUPABASE_URL,
        supabase_key=Config.SUPABASE_KEY,
        gcp_project_id=Config.GCP_PROJECT_ID,
        gcs_bucket_name=Config.GCS_BUCKET_NAME,
    )
