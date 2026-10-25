import io
import zipfile
from pathlib import Path
import pytest

from pipeline.extract import parse_chat_log, extract_whatsapp_archive, ChatMessage


SAMPLE_ANDROID_CHAT = """23/10/2026, 08:14 - Dadu: Morning everyone!
23/10/2026, 08:15 - Dadu: PTT-20261023-WA0001.opus (file attached)
23/10/2026, 08:16 - Ma: Forwarded: PTT-20261023-WA0002.opus (file attached)
23/10/2026, 09:30 - Rahul: I will reach Kolkata by 5 PM.
"""

SAMPLE_IOS_CHAT = """[23/10/26, 8:14:15 PM] Dadu: ‎<attached: audio_ios_1.opus>
[23/10/26, 8:15:20 PM] Ma: Forwarded message: ‎<attached: audio_ios_2.opus>
[23/10/26, 8:30:00 PM] Babai: Dinner will be ready.
"""

def test_parse_android_chat_log():
    messages = parse_chat_log(SAMPLE_ANDROID_CHAT)
    assert len(messages) == 4

    # Message 1
    assert messages[0].sender == "Dadu"
    assert messages[0].timestamp_str == "23/10/2026, 08:14"
    assert messages[0].attachment is None
    assert not messages[0].is_forwarded

    # Message 2 - Audio attached
    assert messages[1].sender == "Dadu"
    assert messages[1].attachment == "PTT-20261023-WA0001.opus"
    assert messages[1].is_voice_note
    assert not messages[1].is_forwarded

    # Message 3 - Forwarded audio
    assert messages[2].sender == "Ma"
    assert messages[2].attachment == "PTT-20261023-WA0002.opus"
    assert messages[2].is_voice_note
    assert messages[2].is_forwarded

def test_parse_ios_chat_log():
    messages = parse_chat_log(SAMPLE_IOS_CHAT)
    assert len(messages) == 3

    assert messages[0].sender == "Dadu"
    assert messages[0].attachment == "audio_ios_1.opus"
    assert messages[0].is_voice_note
    assert not messages[0].is_forwarded

    assert messages[1].sender == "Ma"
    assert messages[1].attachment == "audio_ios_2.opus"
    assert messages[1].is_voice_note
    assert messages[1].is_forwarded

def test_extract_whatsapp_archive(tmp_path):
    # Create a synthetic zip with _chat.txt and a dummy audio file
    zip_path = tmp_path / "whatsapp_export.zip"
    audio_content = b"RIFF....WAVEfmt ...."

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("_chat.txt", SAMPLE_ANDROID_CHAT)
        zf.writestr("PTT-20261023-WA0001.opus", audio_content)
        zf.writestr("PTT-20261023-WA0002.opus", audio_content)

    output_dir = tmp_path / "extracted"
    messages, voice_notes = extract_whatsapp_archive(zip_path, output_dir, normalize=False)

    assert len(messages) == 4
    assert len(voice_notes) == 2
    assert voice_notes[0].sender == "Dadu"
    assert not voice_notes[0].is_forwarded
    assert voice_notes[0].audio_path.exists()
    assert voice_notes[1].is_forwarded

def test_parse_skips_encryption_notice():
    chat = """23/10/2026, 08:14 - Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen to them.
23/10/2026, 08:15 - Dadu: Good morning!
"""
    messages = parse_chat_log(chat)
    assert len(messages) == 1
    assert messages[0].sender == "Dadu"
    assert "end-to-end encrypted" not in messages[0].text

def test_extract_bracketed_audio_filename(tmp_path):
    zip_path = tmp_path / "bracketed_export.zip"
    chat_content = "23/10/2026, 08:15 - Dadu: audio [1].m4a (file attached)\n"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("_chat.txt", chat_content)
        zf.writestr("audio [1].m4a", b"RIFF....")

    output_dir = tmp_path / "extracted"
    messages, voice_notes = extract_whatsapp_archive(zip_path, output_dir, normalize=False)
    assert len(voice_notes) == 1
    assert voice_notes[0].filename == "audio [1].m4a"
    assert voice_notes[0].audio_path.name == "audio [1].m4a"


def test_extract_prioritizes_chat_txt_over_auxiliary_txt(tmp_path):
    zip_path = tmp_path / "android_export.zip"
    chat_content = "23/10/2026, 08:15 - Dadu: Hello family!\n"
    readme_content = "This is a readme file that is not a chat log."

    with zipfile.ZipFile(zip_path, "w") as zf:
        # Put AAA_README.txt first alphabetically to ensure it would be returned by naive glob
        zf.writestr("AAA_README.txt", readme_content)
        zf.writestr("WhatsApp Chat with Family.txt", chat_content)

    output_dir = tmp_path / "extracted"
    messages, voice_notes = extract_whatsapp_archive(zip_path, output_dir, normalize=False)
    assert len(messages) == 1
    assert messages[0].sender == "Dadu"
    assert messages[0].text == "Hello family!"
