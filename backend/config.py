"""
Backend Configuration
=====================
Loads configuration from the shared /config.yaml file.
Secrets are loaded from environment variables (.env).

To find settings:
  - AI models & processing → config.yaml → backend section
  - Prompts → config.yaml → prompts section
  - Secrets (API keys) → .env file
"""

import os
from pathlib import Path

import yaml

# Load YAML config
# In production (Docker), config.yaml is copied to /app/config.yaml (same dir as this file)
# In development, it's in the project root (../config.yaml)
current_dir = Path(__file__).parent
_config_path = current_dir / "config.yaml"

if not _config_path.exists():
    _config_path = current_dir.parent / "config.yaml"

if not _config_path.exists():
    raise FileNotFoundError(f"config.yaml not found in {current_dir} or {current_dir.parent}")

with open(_config_path) as f:
    _raw_config = yaml.safe_load(f)


class Config:
    """Application configuration loaded from config.yaml + environment."""

    # === SECRETS (from .env) ===
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_REGION = os.getenv("GCP_REGION")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    
    # CORS (can be overridden by env for different environments)
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

    # === PROCESSING (from config.yaml) ===
    _backend = _raw_config.get("backend", {})
    _processing = _backend.get("processing", {})
    
    MAX_CONCURRENT_SEGMENTS: int = _processing.get("maxConcurrentSegments", 5)
    HTTP_TIMEOUT: float = _processing.get("httpTimeoutSeconds", 30.0)
    SEGMENT_BATCH_SIZE: int = _processing.get("segmentBatchSize", 50)

    # === AI MODELS (from config.yaml) ===
    _ai = _backend.get("ai", {})
    _models = _ai.get("models", {})
    
    GEMINI_MODEL_TEXT_CLEANING: str = _models.get("textCleaning", "gemini-3-pro-preview")
    GEMINI_MODEL_QA: str = _models.get("qa", "gemini-2.5-flash-preview")

    # === TTS (from config.yaml) ===
    _tts = _backend.get("tts", {})
    
    TTS_VOICE_NAME: str = _tts.get("voiceName", "en-US-Chirp3-HD-Aoede")
    TTS_LANGUAGE_CODE: str = _tts.get("languageCode", "en-US")
    TTS_SPEAKING_RATE: float = _tts.get("speakingRate", 1.0)


class Prompts:
    """Prompts loaded from config.yaml."""
    
    _prompts = _raw_config.get("prompts", {})
    
    TEXT_CLEANING: str = _prompts.get("textCleaning", "")
    QA_WITH_AUDIO: str = _prompts.get("qaWithAudio", "")
