import wave
import struct
import math
from pathlib import Path
import pytest

from pipeline.vad import is_speech

@pytest.fixture
def silence_wav(tmp_path) -> Path:
    """Generate 0.5s of pure silence (16kHz mono 16-bit)."""
    wav_path = tmp_path / "silence.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # All zeros
        wf.writeframes(b"\x00" * int(16000 * 0.5 * 2))
    return wav_path

@pytest.fixture
def tone_wav(tmp_path) -> Path:
    """Generate 0.5s of strong audible audio (16kHz mono 16-bit)."""
    wav_path = tmp_path / "tone.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        frames = []
        for i in range(int(16000 * 0.5)):
            val = int(32767 * 0.4 * math.sin(2 * math.pi * 440 * i / 16000))
            frames.append(struct.pack("<h", val))
        wf.writeframes(b"".join(frames))
    return wav_path

def test_vad_detects_silence(silence_wav):
    has_speech, energy = is_speech(silence_wav)
    assert not has_speech
    assert energy < 0.005

def test_vad_detects_audible_signal(tone_wav):
    has_speech, energy = is_speech(tone_wav)
    assert has_speech
    assert energy > 0.01

def test_vad_missing_file():
    with pytest.raises(FileNotFoundError):
        is_speech("nonexistent_path/silence.wav")

def test_vad_non_wav_graceful_handling(tmp_path):
    dummy_opus = tmp_path / "voice.opus"
    dummy_opus.write_bytes(b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00")
    has_speech, energy = is_speech(dummy_opus)
    assert has_speech is True
    assert energy == 1.0
