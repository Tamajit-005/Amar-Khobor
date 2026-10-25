import json
import os
import zipfile
from pathlib import Path
import pytest

from pipeline.run import run_pipeline


@pytest.fixture
def mock_whatsapp_zip(tmp_path) -> Path:
    zip_path = tmp_path / "chat_export.zip"
    chat_txt = """23/10/2026, 08:14 - Dadu: PTT-001.opus (file attached)
23/10/2026, 08:15 - Ma: Forwarded: PTT-002.opus (file attached)
23/10/2026, 08:30 - Rahul: PTT-003.opus (file attached)
"""
    # Create minimal 16k mono wav bytes so ffmpeg and vad can process it
    import wave
    import struct
    import math

    def make_wav_bytes(is_tone: bool = True) -> bytes:
        import io
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            frames = []
            for i in range(int(16000 * 0.2)):
                amp = 32767 * 0.4 if is_tone else 0
                val = int(amp * math.sin(2 * math.pi * 440 * i / 16000))
                frames.append(struct.pack("<h", val))
            wf.writeframes(b"".join(frames))
        return buf.getvalue()

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("_chat.txt", chat_txt)
        zf.writestr("PTT-001.opus", make_wav_bytes(True))   # Tone (audible)
        zf.writestr("PTT-002.opus", make_wav_bytes(True))   # Tone (forwarded)
        zf.writestr("PTT-003.opus", make_wav_bytes(False))  # Silence (noise/vad skip)

    return zip_path


def test_end_to_end_pipeline_run(mock_whatsapp_zip, tmp_path):
    os.environ["MOCK_MODE"] = "true"
    out_dir = tmp_path / "output"

    result = run_pipeline(
        archive_path=mock_whatsapp_zip,
        provider_name="saaras",
        tts_engine="edge-tts",
        output_dir=out_dir,
    )

    assert result["status"] == "success"
    assert result["provider"] == "saaras"
    assert result["tts_engine"] == "edge-tts"
    assert "spoken_script" in result
    assert "show_notes" in result
    assert Path(result["audio_path"]).exists()

    # Check output json file
    json_path = out_dir / "digest.json"
    assert json_path.exists()
    saved_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved_data["spoken_script"] == result["spoken_script"]

    # Forwarded chain spam is skipped before STT and never enters the digest
    forwarded = [t for t in result["transcripts"] if t["is_forwarded"]]
    assert len(forwarded) == 1
    assert forwarded[0]["text"] == "[forwarded_skipped]"
    assert forwarded[0]["skipped_forwarded"] is True
    assert all(note["sender"] != "Ma" for note in result["show_notes"])
