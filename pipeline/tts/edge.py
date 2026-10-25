import asyncio
import os
from pathlib import Path
from typing import Optional

from pipeline import is_mock_mode
from pipeline.tts.base import TTSProvider, write_mock_audio


DEFAULT_EDGE_VOICE = "bn-IN-BashkarNeural"  # High quality Bengali male neural voice; alternative: "bn-IN-TanishaaNeural"


class EdgeTTSProvider(TTSProvider):
    def __init__(self, default_voice: Optional[str] = None):
        self.default_voice = default_voice or os.getenv("EDGE_TTS_VOICE", DEFAULT_EDGE_VOICE)

    @property
    def provider_name(self) -> str:
        return "edge-tts"

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

        import edge_tts

        selected_voice = voice or self.default_voice

        async def _run_edge():
            communicate = edge_tts.Communicate(text, selected_voice)
            await communicate.save(str(out))

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an async event loop (e.g. inside FastAPI handler)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(lambda: asyncio.run(_run_edge())).result()
            else:
                loop.run_until_complete(_run_edge())
        except RuntimeError:
            asyncio.run(_run_edge())

        return out
