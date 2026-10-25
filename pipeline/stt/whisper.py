import os
import time
from pathlib import Path
from typing import Optional
import httpx

from pipeline import is_mock_mode, require_key
from pipeline.stt.base import STTProvider, STTResult


MOCK_WHISPER_TRANSCRIPTS = {
    "bn-IN": "দাদু বললেন প্রেসারের ওষুধ আজকে নিয়ে আসতে।",
    "hi-IN": "कल शाम को सब लोग घर जल्दी आ जाना।",
    "en-IN": "Flight lands at terminal 2 by 4:30 PM tomorrow.",
    "benglish": "কালকে বিকেলে ফ্লাইট আছে আর মেডিসিনটা কালেক্ট করে নিও।",
    "hinglish": "कल शाम को मीटिंग है और टिकट बुक कर लेना प्लीज।",
    "noise": "Thank you for watching! Subscribe for more.",
}


class WhisperSTT(STTProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model or os.getenv("WHISPER_MODEL", "whisper-large-v3")
        self.api_url = api_url or os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/audio/transcriptions")

    @property
    def provider_name(self) -> str:
        return "whisper"

    @property
    def model_name(self) -> str:
        return self.model

    def transcribe(
        self,
        audio_path: str | Path,
        language_mode: str = "bn-IN",
        language_hint: Optional[str] = None,
    ) -> STTResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        start_time = time.perf_counter()

        if is_mock_mode():
            text = MOCK_WHISPER_TRANSCRIPTS.get(
                language_mode,
                "দাদু বললেন কালকে প্রেসারের ওষুধটা নিয়ে আসতে হবে।",
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000) or 95
            return STTResult(
                text=text,
                latency_ms=latency_ms,
                char_count=len(text),
                language_detected=language_mode[:2],
                no_speech_prob=0.005,
                provider=self.provider_name,
                model=self.model_name,
                language_mode=language_mode,
            )

        url = self.api_url
        api_key = self.api_key or require_key("GROQ_API_KEY", "Groq Whisper")
        headers = {"Authorization": f"Bearer {api_key}"}

        # Language code conversion for Whisper (2-letter ISO: "bn", "hi", "en")
        whisper_lang = language_hint or (language_mode.split("-")[0] if "-" in language_mode else None)

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/wav")}
            data = {
                "model": self.model,
                "response_format": "verbose_json",
            }
            if whisper_lang and whisper_lang in ("bn", "hi", "en"):
                data["language"] = whisper_lang

            response = httpx.post(url, headers=headers, files=files, data=data, timeout=60.0)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if response.status_code != 200:
            raise RuntimeError(
                f"Groq Whisper API Error (HTTP {response.status_code}): {response.text}"
            )

        res_json = response.json()
        transcript = res_json.get("text", "").strip()

        # Extract no_speech_prob if segments available
        segments = res_json.get("segments", [])
        no_speech_prob = None
        if segments and "no_speech_prob" in segments[0]:
            no_speech_prob = float(segments[0]["no_speech_prob"])

        return STTResult(
            text=transcript,
            latency_ms=latency_ms,
            char_count=len(transcript),
            language_detected=res_json.get("language", language_mode),
            no_speech_prob=no_speech_prob,
            provider=self.provider_name,
            model=self.model_name,
            language_mode=language_mode,
        )
