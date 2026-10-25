import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.extract import extract_whatsapp_archive
from pipeline.vad import is_speech
from pipeline.stt.base import get_stt_provider, STTResult
from pipeline.summarize import generate_digest
from pipeline.tts.base import get_tts_provider


def run_pipeline(
    archive_path: str | Path,
    provider_name: Optional[str] = None,
    tts_engine: Optional[str] = None,
    output_dir: Optional[str | Path] = None,
    language_mode: str = "bn-IN",
) -> Dict[str, Any]:
    """
    End-to-end execution of the Amar Khobor processing pipeline:
    1. Unpack WhatsApp export & parse chat log (associating voice notes with senders/timestamps)
    2. Normalize audio clips to 16kHz mono .wav via FFmpeg
    3. Energy-based VAD pre-filter to skip silence/noise clips before STT (saving credits)
    4. Dual STT transcription (Saaras vs Whisper)
    5. Dual-output digest generation (warm spoken_script + structured show_notes)
    6. Audio synthesis via TTS engine (edge-tts for dev, elevenlabs for demo)
    7. Persistence of digest.json and digest.mp3
    """
    archive = Path(archive_path)
    if not archive.exists():
        raise FileNotFoundError(f"WhatsApp archive not found: {archive}")

    active_provider = (provider_name or os.getenv("STT_PROVIDER", "saaras")).lower()
    active_tts = (tts_engine or os.getenv("TTS_ENGINE", "edge-tts")).lower()

    run_id = f"digest_{uuid.uuid4().hex[:8]}"
    out = Path(output_dir) if output_dir else Path("output") / run_id
    out.mkdir(parents=True, exist_ok=True)

    extracted_dir = out / "extracted"
    messages, voice_notes = extract_whatsapp_archive(archive, extracted_dir, normalize=True)

    stt = get_stt_provider(active_provider)
    transcripts: List[Dict[str, Any]] = []

    for vn in voice_notes:
        # Forwarded chain spam: skipped before any paid STT call, and filtered from the digest.
        if vn.is_forwarded:
            transcripts.append(
                {
                    "clip_id": vn.clip_id,
                    "sender": vn.sender,
                    "timestamp_str": vn.timestamp_str,
                    "filename": vn.filename,
                    "text": "[forwarded_skipped]",
                    "skipped_forwarded": True,
                    "is_forwarded": True,
                    "provider": stt.provider_name,
                    "model": stt.model_name,
                }
            )
            continue

        target_audio = vn.normalized_path if vn.normalized_path and vn.normalized_path.exists() else vn.audio_path

        # Step 3: VAD Pre-Filter
        has_speech, energy = is_speech(target_audio)
        if not has_speech:
            # Sub-threshold clip skipped prior to STT call to conserve credits
            transcripts.append(
                {
                    "clip_id": vn.clip_id,
                    "sender": vn.sender,
                    "timestamp_str": vn.timestamp_str,
                    "filename": vn.filename,
                    "text": "[background_noise]",
                    "skipped_vad": True,
                    "energy": energy,
                    "is_forwarded": vn.is_forwarded,
                    "provider": stt.provider_name,
                    "model": stt.model_name,
                }
            )
            continue

        # Step 4: STT Transcription
        stt_res: STTResult = stt.transcribe(target_audio, language_mode=language_mode)

        # Secondary check: if provider returned no_speech_prob > 0.8
        if stt_res.no_speech_prob is not None and stt_res.no_speech_prob > 0.8:
            text = "[background_noise]"
        else:
            text = stt_res.text

        transcripts.append(
            {
                "clip_id": vn.clip_id,
                "sender": vn.sender,
                "timestamp_str": vn.timestamp_str,
                "filename": vn.filename,
                "text": text,
                "skipped_vad": False,
                "energy": energy,
                "is_forwarded": vn.is_forwarded,
                "latency_ms": stt_res.latency_ms,
                "char_count": stt_res.char_count,
                "provider": stt_res.provider,
                "model": stt_res.model,
                "language_mode": stt_res.language_mode,
            }
        )

    # Step 5: Dual-Output Digest Generation
    digest = generate_digest(transcripts)

    # Step 6: TTS Audio Synthesis
    tts = get_tts_provider(active_tts)
    audio_output_path = out / "digest.mp3"
    tts.synthesize(digest.spoken_script, audio_output_path)

    # Step 7: Save structured JSON artifacts
    result_data = {
        "status": "success",
        "run_id": run_id,
        "provider": active_provider,
        "tts_engine": active_tts,
        "language_mode": language_mode,
        "total_messages": len(messages),
        "total_voice_notes": len(voice_notes),
        "transcripts": transcripts,
        "spoken_script": digest.spoken_script,
        "show_notes": [note.model_dump() for note in digest.show_notes],
        "audio_path": str(audio_output_path),
    }

    json_output_path = out / "digest.json"
    json_output_path.write_text(json.dumps(result_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return result_data


def main():
    parser = argparse.ArgumentParser(description="Amar Khobor Audio Briefing Pipeline")
    parser.add_argument("archive", help="Path to WhatsApp export .zip or folder")
    parser.add_argument("--provider", choices=["saaras", "whisper"], default=None, help="STT provider")
    parser.add_argument("--tts", choices=["edge-tts", "elevenlabs"], default=None, help="TTS engine")
    parser.add_argument("--out-dir", default=None, help="Directory to store output artifacts")
    parser.add_argument("--lang", default="bn-IN", help="Language mode (bn-IN, hi-IN, en-IN, benglish, hinglish)")

    args = parser.parse_args()

    try:
        res = run_pipeline(
            archive_path=args.archive,
            provider_name=args.provider,
            tts_engine=args.tts,
            output_dir=args.out_dir,
            language_mode=args.lang,
        )
        print("\n--- Amar Khobor Digest Completed Successfully ---")
        print(f"Provider:   {res['provider']}")
        print(f"TTS Engine: {res['tts_engine']}")
        print(f"Audio:      {res['audio_path']}")
        print("\n[Spoken Script]:")
        print(res["spoken_script"])
        print("\n[Show Notes Receipts]:")
        for note in res["show_notes"]:
            urgent_badge = " [URGENT]" if note.get("urgent") else ""
            print(f"- ({note['category'].upper()}{urgent_badge}) {note['sender']}: {note['claim']}")
    except Exception as e:
        print(f"Pipeline Execution Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
