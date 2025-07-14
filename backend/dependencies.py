from typing import Optional

from .services.transcription import WhisperTranscriber
from .services.llm import LLMClient
from .services.tts import TTSClient

# Global service instances; initialized in backend.main lifespan
transcription_service: Optional[WhisperTranscriber] = None
llm_service: Optional[LLMClient] = None
tts_service: Optional[TTSClient] = None


def get_transcription_service() -> WhisperTranscriber:
    """Return the globally initialized transcription service."""
    return transcription_service


def get_llm_service() -> LLMClient:
    """Return the globally initialized LLM service."""
    return llm_service


def get_tts_service() -> TTSClient:
    """Return the globally initialized TTS service."""
    return tts_service
