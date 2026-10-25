import asyncio
import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.db import db
from pipeline.run import run_pipeline


app = FastAPI(
    title="Amar Khobor API",
    description="Multilingual Family WhatsApp Overnight Audio Briefing System",
    version="1.0.0",
)

# Enable CORS for the Next.js frontend only (override with ALLOWED_ORIGINS).
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

# Guard against disk-filling uploads (zip bomb defence starts here).
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(500 * 1024 * 1024)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SettingsPayload(BaseModel):
    stt_provider: Optional[str] = None
    tts_engine: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "ok", "mock_mode": settings.MOCK_MODE}


@app.get("/settings")
def get_settings():
    return {
        "stt_provider": settings.STT_PROVIDER,
        "tts_engine": settings.TTS_ENGINE,
        "sarvam_model": settings.SARVAM_MODEL,
        "whisper_model": settings.WHISPER_MODEL,
        "gemma_model": settings.GEMMA_MODEL,
        "elevenlabs_model": settings.ELEVENLABS_MODEL_ID,
        "mock_mode": settings.MOCK_MODE,
    }


_settings_lock = asyncio.Lock()


@app.post("/settings")
async def update_settings(payload: SettingsPayload):
    async with _settings_lock:
        if payload.stt_provider:
            if payload.stt_provider not in ("saaras", "whisper"):
                raise HTTPException(status_code=400, detail="Invalid stt_provider. Choose 'saaras' or 'whisper'.")
            settings.STT_PROVIDER = payload.stt_provider
            os.environ["STT_PROVIDER"] = payload.stt_provider

        if payload.tts_engine:
            if payload.tts_engine not in ("edge-tts", "elevenlabs"):
                raise HTTPException(status_code=400, detail="Invalid tts_engine. Choose 'edge-tts' or 'elevenlabs'.")
            settings.TTS_ENGINE = payload.tts_engine
            os.environ["TTS_ENGINE"] = payload.tts_engine

    return {
        "stt_provider": settings.STT_PROVIDER,
        "tts_engine": settings.TTS_ENGINE,
        "mock_mode": settings.MOCK_MODE,
    }


async def _process_digest_task(
    digest_id: str,
    archive_path: Path,
    output_dir: Path,
    language_mode: str,
    provider: str,
    tts_engine: str,
    temp_dir: Optional[Path] = None,
):
    try:
        # Offload CPU/IO intensive audio pipeline to a thread pool to avoid blocking the event loop
        res = await asyncio.to_thread(
            run_pipeline,
            archive_path=archive_path,
            provider_name=provider,
            tts_engine=tts_engine,
            output_dir=output_dir,
            language_mode=language_mode,
        )

        audio_file = Path(res["audio_path"])
        db_record = {
            "id": digest_id,
            "status": "ready",
            "provider": provider,
            "tts_engine": tts_engine,
            "language_mode": language_mode,
            "spoken_script": res["spoken_script"],
            "show_notes": res["show_notes"],
            "transcripts": res["transcripts"],
            "audio_path": str(audio_file),
            "audio_url": f"/audio/{digest_id}",
        }
        await db.save_digest(db_record)

        # Clean up intermediate unzipped extracted files to free disk space
        extracted_dir = output_dir / "extracted"
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir, ignore_errors=True)
    except Exception as e:
        error_record = {
            "id": digest_id,
            "status": "failed",
            "error": str(e),
            "provider": provider,
            "tts_engine": tts_engine,
        }
        await db.save_digest(error_record)
    finally:
        # Clean up temporary directory containing uploaded archive completely
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        elif archive_path.exists():
            try:
                archive_path.unlink()
            except OSError:
                pass


@app.post("/digests/run", status_code=status.HTTP_202_ACCEPTED)
async def create_digest_run(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language_mode: str = Form("bn-IN"),
):
    """
    Non-blocking async ingestion endpoint.
    Returns HTTP 202 Accepted immediately. Client polls GET /digests/{digest_id}.
    """
    digest_id = f"digest_{uuid.uuid4().hex[:8]}"

    # Prepare temp workdir with sanitized filename
    safe_filename = Path(file.filename or "upload.zip").name
    temp_dir = Path(tempfile.mkdtemp(prefix="amarkhobor_"))
    archive_path = temp_dir / safe_filename

    copied = 0
    try:
        with open(archive_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                copied += len(chunk)
                if copied > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
                    )
                buffer.write(chunk)

        # Fail the request instead of accepting a job that cannot succeed.
        if not zipfile.is_zipfile(archive_path):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid .zip export.")
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    output_dir = Path("output") / digest_id
    output_dir.mkdir(parents=True, exist_ok=True)

    initial_record = {
        "id": digest_id,
        "status": "processing",
        "provider": settings.STT_PROVIDER,
        "tts_engine": settings.TTS_ENGINE,
        "language_mode": language_mode,
    }
    await db.save_digest(initial_record)

    # Invariant: FastAPI BackgroundTasks execution
    background_tasks.add_task(
        _process_digest_task,
        digest_id=digest_id,
        archive_path=archive_path,
        output_dir=output_dir,
        language_mode=language_mode,
        provider=settings.STT_PROVIDER,
        tts_engine=settings.TTS_ENGINE,
        temp_dir=temp_dir,
    )

    return {
        "digest_id": digest_id,
        "status": "processing",
        "provider": settings.STT_PROVIDER,
        "tts_engine": settings.TTS_ENGINE,
        "poll_url": f"/digests/{digest_id}",
    }


@app.post("/digests/run-nightly", status_code=status.HTTP_202_ACCEPTED)
async def create_nightly_digest_run(
    background_tasks: BackgroundTasks,
    language_mode: str = Form("bn-IN"),
):
    """
    Automated overnight briefing run (e.g. triggered via 6:00 AM cron).
    Processes the most recent WhatsApp chat export from data/nightly/ or fallback sample_chat.zip.
    """
    nightly_dir = Path("data/nightly")
    candidates = (
        sorted(nightly_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        if nightly_dir.exists()
        else []
    )
    if candidates:
        archive_path = candidates[0]
    else:
        archive_path = Path("test_data/sample_chat.zip")
        if not archive_path.exists():
            raise HTTPException(status_code=404, detail="No WhatsApp archive available for nightly digest.")

    digest_id = f"nightly_{uuid.uuid4().hex[:8]}"
    temp_dir = Path(tempfile.mkdtemp(prefix="amarkhobor_nightly_"))
    staged_archive = temp_dir / archive_path.name
    shutil.copy2(archive_path, staged_archive)

    output_dir = Path("output") / digest_id
    output_dir.mkdir(parents=True, exist_ok=True)

    initial_record = {
        "id": digest_id,
        "status": "processing",
        "provider": settings.STT_PROVIDER,
        "tts_engine": settings.TTS_ENGINE,
        "language_mode": language_mode,
        "trigger": "nightly_cron",
    }
    await db.save_digest(initial_record)

    background_tasks.add_task(
        _process_digest_task,
        digest_id=digest_id,
        archive_path=staged_archive,
        output_dir=output_dir,
        language_mode=language_mode,
        provider=settings.STT_PROVIDER,
        tts_engine=settings.TTS_ENGINE,
        temp_dir=temp_dir,
    )

    return {
        "digest_id": digest_id,
        "status": "processing",
        "provider": settings.STT_PROVIDER,
        "tts_engine": settings.TTS_ENGINE,
        "poll_url": f"/digests/{digest_id}",
        "source_archive": archive_path.name,
    }


@app.get("/digests/{digest_id}")
async def get_digest(digest_id: str):
    record = await db.get_digest(digest_id)
    if not record:
        raise HTTPException(status_code=404, detail="Digest not found")
    return record


@app.get("/digests")
async def list_digests():
    return await db.list_digests()


@app.get("/audio/{digest_id}")
async def get_digest_audio(digest_id: str):
    record = await db.get_digest(digest_id)
    if not record:
        raise HTTPException(status_code=404, detail="Digest not found")

    audio_path = record.get("audio_path")
    if not audio_path or not Path(audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not ready or not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"{digest_id}.mp3",
    )


@app.get("/leaderboard")
async def get_leaderboard():
    return await db.get_leaderboard()
