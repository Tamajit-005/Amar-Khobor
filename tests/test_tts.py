import os
from pathlib import Path
import pytest

from pipeline.tts.base import TTSProvider, get_tts_provider
from pipeline.tts.edge import EdgeTTSProvider
from pipeline.tts.eleven import ElevenLabsTTSProvider


def test_tts_factory():
    p1 = get_tts_provider("edge-tts")
    assert isinstance(p1, EdgeTTSProvider)
    assert p1.provider_name == "edge-tts"

    p2 = get_tts_provider("elevenlabs")
    assert isinstance(p2, ElevenLabsTTSProvider)
    assert p2.provider_name == "elevenlabs"

    with pytest.raises(ValueError):
        get_tts_provider("unknown_engine")


def test_edge_tts_mock_synthesis(tmp_path):
    os.environ["MOCK_MODE"] = "true"
    out = tmp_path / "edge_output.mp3"

    provider = EdgeTTSProvider()
    res = provider.synthesize("শুভ সকাল! আজকের খবরের ব্রিফিংয়ে সবাইকে স্বাগতম।", out)

    assert res.exists()
    assert res.stat().st_size > 0


def test_elevenlabs_mock_synthesis(tmp_path):
    os.environ["MOCK_MODE"] = "true"
    out = tmp_path / "eleven_output.mp3"

    provider = ElevenLabsTTSProvider()
    res = provider.synthesize("Good morning! Here is your daily family digest.", out)

    assert res.exists()
    assert res.stat().st_size > 0
