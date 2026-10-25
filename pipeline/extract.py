import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from pipeline.normalize import normalize_audio


AUDIO_EXTENSIONS = {".opus", ".m4a", ".mp3", ".wav", ".ogg", ".aac"}

# Android: "23/10/2026, 08:14 - Dadu: message"
ANDROID_MSG_RE = re.compile(
    r"^(\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4},\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s+-\s+([^:]+?):\s+(.*)$"
)

# iOS: "[23/10/26, 8:14:15 PM] Dadu: message"
IOS_MSG_RE = re.compile(
    r"^\[(\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4},\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s+([^:]+?):\s+(.*)$"
)

# Attachment patterns
ATTACHMENT_RES = [
    re.compile(r"<attached:\s*([^>]+)>"),
    re.compile(r"([a-zA-Z0-9_\-\.\s\[\]\(\)]+?\.(?:opus|m4a|mp3|wav|ogg|aac))\s*\(file attached\)", re.IGNORECASE),
    re.compile(r"([a-zA-Z0-9_\-\.\s\[\]\(\)]+?\.(?:opus|m4a|mp3|wav|ogg|aac))\s*<attached>", re.IGNORECASE),
]


@dataclass
class ChatMessage:
    timestamp_str: str
    sender: str
    text: str
    attachment: Optional[str] = None
    is_forwarded: bool = False
    is_voice_note: bool = False


@dataclass
class VoiceNoteItem:
    clip_id: str
    sender: str
    timestamp_str: str
    filename: str
    audio_path: Path
    normalized_path: Optional[Path] = None
    is_forwarded: bool = False


def _clean_unicode_artifacts(text: str) -> str:
    # WhatsApp exports often contain invisible directional/mark characters
    return text.replace("‎", "").replace("‏", "").replace("\xa0", " ").strip()


def parse_chat_log(content: str) -> List[ChatMessage]:
    messages: List[ChatMessage] = []
    lines = content.splitlines()

    for line in lines:
        cleaned_line = _clean_unicode_artifacts(line)
        if not cleaned_line:
            continue

        match = ANDROID_MSG_RE.match(cleaned_line) or IOS_MSG_RE.match(cleaned_line)
        if not match:
            # Skip system notices (encryption notice, admin events) instead of appending to prior sender
            if any(k in cleaned_line for k in ["end-to-end encrypted", "created group", "added you", "changed the subject"]):
                continue
            # Multi-line message continuation; append to last message if present
            if messages:
                messages[-1].text += "\n" + cleaned_line
            continue

        timestamp_str, sender, text = match.groups()
        sender = sender.strip()
        text = text.strip()

        # Check forwarded indicator
        is_forwarded = bool(re.search(r"\bforwarded\b", text, re.IGNORECASE))

        # Check for attachment
        attachment = None
        for att_re in ATTACHMENT_RES:
            att_match = att_re.search(text)
            if att_match:
                attachment = att_match.group(1).strip()
                break

        is_voice_note = False
        if attachment:
            ext = Path(attachment).suffix.lower()
            is_voice_note = ext in AUDIO_EXTENSIONS

        messages.append(
            ChatMessage(
                timestamp_str=timestamp_str.strip(),
                sender=sender,
                text=text,
                attachment=attachment,
                is_forwarded=is_forwarded,
                is_voice_note=is_voice_note,
            )
        )

    return messages


def extract_whatsapp_archive(
    archive_path: str | Path,
    output_dir: str | Path,
    normalize: bool = True,
) -> Tuple[List[ChatMessage], List[VoiceNoteItem]]:
    """
    Extracts a WhatsApp export .zip and matches voice note files
    to senders and timestamps exclusively from _chat.txt.
    """
    archive = Path(archive_path)
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)

    if not archive.exists():
        raise FileNotFoundError(f"WhatsApp archive not found: {archive}")

    with zipfile.ZipFile(archive, "r") as zf:
        try:
            zf.extractall(dest, filter="data")
        except TypeError:
            zf.extractall(dest)

    # Locate chat log file: prefer _chat.txt, then any file with 'chat' in its name (standard Android), then fallback *.txt
    chat_log_candidates = (
        list(dest.rglob("_chat.txt"))
        or [p for p in dest.rglob("*.txt") if "chat" in p.name.lower()]
        or list(dest.rglob("*.txt"))
    )
    if not chat_log_candidates:
        raise ValueError(f"No chat log (_chat.txt) found in {archive}")

    chat_file = chat_log_candidates[0]
    chat_text = chat_file.read_text(encoding="utf-8", errors="replace")
    messages = parse_chat_log(chat_text)

    voice_notes: List[VoiceNoteItem] = []
    clip_counter = 1

    for msg in messages:
        if not msg.is_voice_note or not msg.attachment:
            continue

        # Match exact filename to avoid glob pattern errors on bracketed filenames (e.g. [audio].m4a)
        att_lower = msg.attachment.lower()
        audio_candidates = [p for p in dest.rglob("*") if p.is_file() and p.name.lower() == att_lower]

        if not audio_candidates:
            continue

        raw_audio_path = audio_candidates[0]
        clip_id = f"clip_{clip_counter:03d}"
        clip_counter += 1

        normalized_path = None
        if normalize and raw_audio_path.exists():
            norm_target = dest / "normalized" / f"{clip_id}_{raw_audio_path.stem}.wav"
            normalized_path = normalize_audio(raw_audio_path, norm_target)

        voice_notes.append(
            VoiceNoteItem(
                clip_id=clip_id,
                sender=msg.sender,
                timestamp_str=msg.timestamp_str,
                filename=msg.attachment,
                audio_path=raw_audio_path,
                normalized_path=normalized_path,
                is_forwarded=msg.is_forwarded,
            )
        )

    return messages, voice_notes
