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
    ENABLE_CHINESE_PROCESSING: bool = _processing.get("enableChineseProcessing", True)
    _consolidation = _processing.get("consolidation", {})
    _discord_mode_raw = _consolidation.get("discordMode", "off")
    DISCORD_CONSOLIDATION_MODE: str = (
        _discord_mode_raw if _discord_mode_raw in {"off", "recap_only"} else "off"
    )
    REDDIT_LIGHT_DEDUP: bool = _consolidation.get("redditLightDedup", False)

    # === AI MODELS (from config.yaml) ===
    _ai = _backend.get("ai", {})
    _models = _ai.get("models", {})
    
    GEMINI_MODEL_TEXT_CLEANING: str = _models.get("textCleaning", "gemini-3-pro-preview")
    GEMINI_MODEL_QA: str = _models.get("qa", "gemini-2.5-flash-preview")

    # === TTS (from config.yaml) ===
    _tts = _backend.get("tts", {})
    _tts_en = _tts.get("en", {})
    _tts_zh = _tts.get("zh", {})

    TTS_VOICE_NAME_EN: str = _tts_en.get("voiceName", "en-US-Chirp3-HD-Aoede")
    TTS_LANGUAGE_CODE_EN: str = _tts_en.get("languageCode", "en-US")
    TTS_VOICE_NAME_ZH: str = _tts_zh.get("voiceName", "cmn-CN-Chirp3-HD-Aoede")
    TTS_LANGUAGE_CODE_ZH: str = _tts_zh.get("languageCode", "cmn-CN")
    TTS_SPEAKING_RATE: float = _tts.get("speakingRate", 1.0)

    @classmethod
    def get_tts_config(cls, language: str = "en") -> tuple[str, str]:
        """Get TTS voice name and language code for the given language."""
        if language == "zh":
            return cls.TTS_VOICE_NAME_ZH, cls.TTS_LANGUAGE_CODE_ZH
        return cls.TTS_VOICE_NAME_EN, cls.TTS_LANGUAGE_CODE_EN

    # === VOICE MODE (from config.yaml) ===
    _voice_mode = _raw_config.get("voiceMode", {})
    _voice_vad = _voice_mode.get("vadSensitivity", {})

    VOICE_MODE_MODEL: str = _voice_mode.get("model", "gemini-live-2.5-flash-native-audio")
    VOICE_MODE_REGION: str = _voice_mode.get("region", "us-central1")
    VOICE_MODE_SESSION_TIMEOUT_MS: int = _voice_mode.get("sessionTimeoutMs", 840000)
    VOICE_MODE_VAD_POSITIVE: float = _voice_vad.get("positiveSpeechThreshold", 0.6)
    VOICE_MODE_VAD_NEGATIVE: float = _voice_vad.get("negativeSpeechThreshold", 0.3)
    VOICE_MODE_VAD_MIN_FRAMES: int = _voice_vad.get("minSpeechFrames", 4)
    VOICE_MODE_RESUME_DELAY_MS: int = _voice_mode.get("resumeDelayMs", 1200)


class Prompts:
    """Prompts loaded from config.yaml."""

    _prompts = _raw_config.get("prompts", {})

    TEXT_CLEANING: str = _prompts.get("textCleaning", "")
    TRANSLATION: str = _prompts.get("translation", "")

    # Language-specific prompts
    _qa_with_audio = _prompts.get("qaWithAudio", {})
    _voice_mode = _prompts.get("voiceMode", {})

    # Handle both old (string) and new (dict) format for backwards compatibility
    if isinstance(_qa_with_audio, str):
        QA_WITH_AUDIO_EN: str = _qa_with_audio
        QA_WITH_AUDIO_ZH: str = _qa_with_audio
    else:
        QA_WITH_AUDIO_EN: str = _qa_with_audio.get("en", "")
        QA_WITH_AUDIO_ZH: str = _qa_with_audio.get("zh", "")

    if isinstance(_voice_mode, str):
        VOICE_MODE_EN: str = _voice_mode
        VOICE_MODE_ZH: str = _voice_mode
    else:
        VOICE_MODE_EN: str = _voice_mode.get("en", "")
        VOICE_MODE_ZH: str = _voice_mode.get("zh", "")

    @classmethod
    def get_qa_prompt(cls, language: str = "en") -> str:
        """Get Q&A prompt for the given language."""
        if language == "zh":
            return cls.QA_WITH_AUDIO_ZH
        return cls.QA_WITH_AUDIO_EN

    @classmethod
    def get_voice_mode_prompt(cls, language: str = "en") -> str:
        """Get voice mode prompt for the given language."""
        if language == "zh":
            return cls.VOICE_MODE_ZH
        return cls.VOICE_MODE_EN
