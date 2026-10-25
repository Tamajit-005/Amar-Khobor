import os
from pathlib import Path
import pytest

from pipeline.stt.base import STTResult, get_stt_provider
from pipeline.stt.saaras import SaarasSTT
from pipeline.stt.whisper import WhisperSTT


def test_stt_result_model():
    result = STTResult(
        text="আমার ওষুধ শেষ হয়ে গেছে।",
        latency_ms=450,
        char_count=23,
        language_detected="bn-IN",
        no_speech_prob=0.01,
        provider="saaras",
        model="saaras:v4",
        language_mode="bn-IN",
    )
    assert result.text == "আমার ওষুধ শেষ হয়ে গেছে।"
    assert result.latency_ms == 450
    assert result.char_count == 23
    assert result.provider == "saaras"


def test_stt_factory():
    p1 = get_stt_provider("saaras")
    assert isinstance(p1, SaarasSTT)

    p2 = get_stt_provider("whisper")
    assert isinstance(p2, WhisperSTT)

    with pytest.raises(ValueError):
        get_stt_provider("unknown_provider")


def test_saaras_mock_transcribe(tmp_path):
    os.environ["MOCK_MODE"] = "true"
    dummy_wav = tmp_path / "test.wav"
    dummy_wav.write_bytes(b"dummy wav data")

    provider = SaarasSTT()
    result = provider.transcribe(dummy_wav, language_mode="bn-IN")

    assert result.provider == "saaras"
    assert len(result.text) > 0
    assert result.char_count == len(result.text)
    assert result.language_mode == "bn-IN"


def test_whisper_mock_transcribe(tmp_path):
    os.environ["MOCK_MODE"] = "true"
    dummy_wav = tmp_path / "test.wav"
    dummy_wav.write_bytes(b"dummy wav data")

    provider = WhisperSTT()
    result = provider.transcribe(dummy_wav, language_mode="benglish")

    assert result.provider == "whisper"
    assert len(result.text) > 0
    assert result.language_mode == "benglish"


def test_live_mode_without_key_fails_loudly(tmp_path, monkeypatch):
    # Live mode must never silently fall back to mock data.
    dummy_wav = tmp_path / "test.wav"
    dummy_wav.write_bytes(b"dummy wav data")
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SARVAM_API_KEY"):
        SaarasSTT(api_key="").transcribe(dummy_wav, language_mode="bn-IN")
