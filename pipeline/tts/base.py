import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


# Bundled silent MP3 so MOCK_MODE runs still produce a playable audio file.
_MOCK_AUDIO = Path("sample_data/sample_demo.mp3")


def write_mock_audio(output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if _MOCK_AUDIO.exists():
        shutil.copyfile(_MOCK_AUDIO, out)
    else:
        # Fallback: minimal MP3 frame header (not playable, never used in a demo)
        out.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1024)
    return out


class TTSProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        voice: Optional[str] = None,
    ) -> Path:
        """Synthesize text into audio and write to output_path."""
        pass


def get_tts_provider(engine_name: Optional[str] = None) -> TTSProvider:
    name = (engine_name or os.getenv("TTS_ENGINE", "edge-tts")).lower().strip()
    if name in ("edge-tts", "edgetts", "edge"):
        from pipeline.tts.edge import EdgeTTSProvider
        return EdgeTTSProvider()
    elif name in ("elevenlabs", "eleven"):
        from pipeline.tts.eleven import ElevenLabsTTSProvider
        return ElevenLabsTTSProvider()
    else:
        raise ValueError(
            f"Unsupported TTS engine: '{name}'. Supported options are 'edge-tts' and 'elevenlabs'."
        )
