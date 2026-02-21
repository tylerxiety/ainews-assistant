"""Shared test fixtures for backend tests."""
import os
import sys
from unittest.mock import patch

import pytest

# Ensure backend/ is on sys.path so imports work regardless of CWD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def processor():
    """Create a NewsletterProcessor with all GCP/Supabase deps mocked."""
    from processor import NewsletterProcessor

    with (
        patch("processor.create_client"),
        patch("processor.vertexai"),
        patch("processor.GenerativeModel"),
        patch("processor.texttospeech.TextToSpeechClient"),
        patch("processor.storage.Client"),
    ):
        proc = NewsletterProcessor(
            supabase_url="http://fake",
            supabase_key="fake",
            gcp_project_id="fake",
            gcs_bucket_name="fake",
        )
    return proc
