import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class STTResult(BaseModel):
    text: str
    latency_ms: int
    char_count: int
    language_detected: Optional[str] = None
    no_speech_prob: Optional[float] = None
    provider: str
    model: str
    language_mode: str


class STTProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def transcribe(
        self,
        audio_path: str | Path,
        language_mode: str = "bn-IN",
    ) -> STTResult:
        """Transcribe an audio file and return an STTResult."""
        pass


def get_stt_provider(provider_name: Optional[str] = None) -> STTProvider:
    """Factory to get the configured STT provider instance."""
    name = (provider_name or os.getenv("STT_PROVIDER", "saaras")).lower().strip()

    if name == "saaras":
        from pipeline.stt.saaras import SaarasSTT
        return SaarasSTT()
    elif name == "whisper":
        from pipeline.stt.whisper import WhisperSTT
        return WhisperSTT()
    else:
        raise ValueError(
            f"Unsupported STT provider: '{name}'. Supported options are 'saaras' and 'whisper'."
        )
