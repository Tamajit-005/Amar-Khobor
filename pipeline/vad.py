import math
import struct
import wave
from pathlib import Path
from typing import Tuple


def is_speech(
    audio_path: str | Path,
    energy_threshold: float = 0.005,
    frame_ms: int = 30,
) -> Tuple[bool, float]:
    """
    Energy-based Voice Activity Detection (VAD) filter.
    Calculates the Root Mean Square (RMS) energy of 16-bit PCM audio.

    Returns:
        (has_speech: bool, mean_rms_energy: float)
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        with wave.open(str(path), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()

            if n_frames == 0:
                return False, 0.0

            raw_bytes = wf.readframes(n_frames)
    except wave.Error:
        # File is not a valid RIFF WAV (e.g. unnormalized .opus or .mp3); assume speech to prevent false drop
        return True, 1.0

    # 16-bit PCM: 2 bytes per sample
    if sampwidth != 2:
        # shortcut: 16-bit PCM standard; for 8-bit or 24-bit, normalize before VAD
        return True, 1.0

    total_samples = n_frames * n_channels
    fmt = f"<{total_samples}h"
    samples = struct.unpack(fmt, raw_bytes)

    # Calculate RMS energy normalized to [0.0, 1.0]
    # Max amplitude for 16-bit signed integer is 32768.0
    sum_squares = sum((s / 32768.0) ** 2 for s in samples)
    mean_energy = math.sqrt(sum_squares / total_samples)

    has_speech = mean_energy >= energy_threshold
    return has_speech, round(mean_energy, 6)
