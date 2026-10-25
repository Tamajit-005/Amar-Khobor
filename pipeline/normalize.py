import os
import subprocess
from pathlib import Path
from typing import Optional


def normalize_audio(
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    target_sample_rate: int = 16000,
) -> Path:
    """
    Normalizes any audio file (e.g. .opus, .m4a, .mp3, .wav)
    to 16kHz 16-bit mono PCM .wav using FFmpeg.
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Input audio file not found: {src}")

    if output_path is None:
        dst = src.with_suffix(".normalized.wav")
    else:
        dst = Path(output_path)

    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ar",
        str(target_sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(dst),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg audio normalization failed (code {result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )

    return dst
