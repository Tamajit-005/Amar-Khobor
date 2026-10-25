import os
from pathlib import Path
from typing import Optional
import httpx

from pipeline import is_mock_mode, require_key
from pipeline.tts.base import TTSProvider, write_mock_audio


DEFAULT_ELEVEN_MODEL = "eleven_v4_turbo"
DEFAULT_ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
# Default multilingual voice (Rachel)
DEFAULT_ELEVEN_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


class ElevenLabsTTSProvider(TTSProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.model_id = model_id or os.getenv("ELEVENLABS_MODEL_ID", DEFAULT_ELEVEN_MODEL)
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVEN_VOICE_ID)
        self.api_url = api_url or os.getenv("ELEVENLABS_API_URL", DEFAULT_ELEVEN_API_URL)

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        voice: Optional[str] = None,
    ) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if is_mock_mode():
            # Mock runs reuse the bundled silent MP3 so the player still works
            return write_mock_audio(out)

        api_key = self.api_key or require_key("ELEVENLABS_API_KEY", "ElevenLabs TTS")
        selected_voice_id = voice or self.voice_id
        url = f"{self.api_url.rstrip('/')}/{selected_voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        if response.status_code != 200:
            raise RuntimeError(
                f"ElevenLabs TTS Error (HTTP {response.status_code}): {response.text}"
            )

        out.write_bytes(response.content)
        return out
