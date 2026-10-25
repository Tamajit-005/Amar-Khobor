import os
import wave
import struct
import math
from pathlib import Path
import pytest

from pipeline.normalize import normalize_audio

@pytest.fixture
def sample_wav(tmp_path) -> Path:
    """Generate a 44100Hz stereo wav file."""
    wav_path = tmp_path / "stereo_44k.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        # Write 0.2 seconds of 440Hz sine wave
        frames = []
        for i in range(int(44100 * 0.2)):
            val = int(32767 * 0.5 * math.sin(2 * math.pi * 440 * i / 44100))
            frames.append(struct.pack("<hh", val, val))
        wf.writeframes(b"".join(frames))
    return wav_path

def test_normalize_audio_to_16k_mono(sample_wav, tmp_path):
    output_wav = tmp_path / "normalized_16k_mono.wav"
    result = normalize_audio(sample_wav, output_wav)

    assert result.exists()
    assert result == output_wav

    with wave.open(str(result), "rb") as wf:
        assert wf.getframerate() == 16000
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2

def test_normalize_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        normalize_audio("nonexistent_path/file.opus")
