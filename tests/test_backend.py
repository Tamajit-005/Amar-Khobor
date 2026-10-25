import os
import zipfile
import pytest
from fastapi.testclient import TestClient

# Ensure MOCK_MODE
os.environ["MOCK_MODE"] = "true"

from backend.main import app

client = TestClient(app)


@pytest.fixture
def sample_zip(tmp_path):
    zip_p = tmp_path / "chat.zip"
    with zipfile.ZipFile(zip_p, "w") as zf:
        zf.writestr("_chat.txt", "23/10/2026, 08:14 - Dadu: Morning everyone!\n")
    return zip_p


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_settings_toggle():
    res = client.get("/settings")
    assert res.status_code == 200
    data = res.json()
    assert "stt_provider" in data
    assert "tts_engine" in data

    # Toggle to whisper and elevenlabs
    post_res = client.post(
        "/settings",
        json={"stt_provider": "whisper", "tts_engine": "elevenlabs"},
    )
    assert post_res.status_code == 200
    updated = post_res.json()
    assert updated["stt_provider"] == "whisper"
    assert updated["tts_engine"] == "elevenlabs"


def test_async_digest_run_and_poll(sample_zip):
    # Upload zip
    with open(sample_zip, "rb") as f:
        response = client.post(
            "/digests/run",
            files={"file": ("chat.zip", f, "application/zip")},
            data={"language_mode": "bn-IN"},
        )

    # Invariant: Must return HTTP 202 Accepted
    assert response.status_code == 202
    data = response.json()
    assert "digest_id" in data
    digest_id = data["digest_id"]
    assert data["status"] in ("processing", "ready")

    # Poll status
    poll_res = client.get(f"/digests/{digest_id}")
    assert poll_res.status_code == 200
    digest_data = poll_res.json()
    assert digest_data["id"] == digest_id
    assert digest_data["status"] in ("processing", "ready")


def test_leaderboard_endpoint():
    res = client.get("/leaderboard")
    assert res.status_code == 200
    assert "saaras" in res.json()


def test_nightly_digest_run():
    response = client.post("/digests/run-nightly", data={"language_mode": "bn-IN"})
    assert response.status_code == 202
    data = response.json()
    assert "digest_id" in data
    assert data["digest_id"].startswith("nightly_")
    assert data["status"] in ("processing", "ready")


def test_initial_sample_demo_audio_not_404():
    response = client.get("/audio/sample_demo")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 0
