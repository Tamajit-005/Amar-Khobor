import os
import time
from pathlib import Path
from typing import Optional
import httpx

from pipeline import is_mock_mode, require_key
from pipeline.stt.base import STTProvider, STTResult


MOCK_TRANSCRIPTS = {
    "bn-IN": "দাদু বললেন ওনার প্রেসারের ওষুধটা যেন আজকে নিয়ে আসা হয়।",
    "hi-IN": "कल शाम को सब लोग घर जल्दी आ जाना, डिनर साथ करेंगे।",
    "en-IN": "Flight lands at terminal 2 by 4:30 PM tomorrow.",
    "benglish": "Kalke bikele flight ache, ar medicine ta collect kore niyo.",
    "hinglish": "Kal shaam ko meeting hai, aur ticket book kar lena please.",
    "noise": "",
}


class SaarasSTT(STTProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        self.model = model or os.getenv("SARVAM_MODEL", "saaras:v4")
        self.api_url = api_url or os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/speech-to-text")

    @property
    def provider_name(self) -> str:
        return "saaras"

    @property
    def model_name(self) -> str:
        return self.model

    def transcribe(
        self,
        audio_path: str | Path,
        language_mode: str = "bn-IN",
    ) -> STTResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        start_time = time.perf_counter()

        if is_mock_mode():
            # Deterministic mock response
            text = MOCK_TRANSCRIPTS.get(
                language_mode,
                "দাদু বললেন কালকে সকালের ওষুধটা যেন তাড়াতাড়ি এনে দেওয়া হয়।",
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000) or 120
            return STTResult(
                text=text,
                latency_ms=latency_ms,
                char_count=len(text),
                language_detected=language_mode,
                no_speech_prob=0.01,
                provider=self.provider_name,
                model=self.model_name,
                language_mode=language_mode,
            )

        # Map language codes for Sarvam Saaras API
        # For code-mixed speech (benglish, hinglish), pass "unknown" so Sarvam's language detection
        # transcribes without forcing monolingual constraints
        if language_mode in ("benglish", "hinglish"):
            lang_code = "unknown"
        elif "-" in language_mode:
            lang_code = language_mode
        else:
            lang_code = "unknown"

        url = self.api_url
        headers = {"api-subscription-key": self.api_key or require_key("SARVAM_API_KEY", "Sarvam Saaras")}

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "audio/wav")}
            data = {
                "model": self.model,
                "language_code": lang_code,
            }

            response = httpx.post(url, headers=headers, files=files, data=data, timeout=60.0)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if response.status_code != 200:
            raise RuntimeError(
                f"Sarvam API Error (HTTP {response.status_code}): {response.text}"
            )

        res_json = response.json()
        transcript = res_json.get("transcript", "")

        return STTResult(
            text=transcript,
            latency_ms=latency_ms,
            char_count=len(transcript),
            language_detected=res_json.get("language_code", language_mode),
            no_speech_prob=res_json.get("no_speech_prob"),
            provider=self.provider_name,
            model=self.model_name,
            language_mode=language_mode,
        )
