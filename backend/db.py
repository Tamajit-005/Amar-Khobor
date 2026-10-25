import asyncio
import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import motor.motor_asyncio
from pymongo.errors import PyMongoError

from backend.config import settings


# Bundled placeholder so the frontend audio player does not 404 on a clean clone.
# Replace with a real ElevenLabs briefing before the demo.
_SAMPLE_AUDIO = Path("sample_data/sample_demo.mp3")

_MEMORY_DIGESTS: Dict[str, Dict[str, Any]] = {
    "sample_demo": {
        "id": "sample_demo",
        "status": "ready",
        "provider": "saaras",
        "tts_engine": "edge-tts",
        "language_mode": "bn-IN",
        "spoken_script": "Good morning family! Here is your quick morning briefing. Dadu reminded everyone that his blood pressure medicine needs to be brought home today. Also, Rahul will be arriving at Kolkata airport this evening, so please make sure a cab is arranged. Wishing everyone a calm and productive day ahead!",
        "show_notes": [
            {
                "claim": "Dadu requested blood pressure medicines to be picked up by noon",
                "sender": "Dadu",
                "timestamp": "Yesterday 8:14 PM",
                "category": "health",
                "urgent": True,
            },
            {
                "claim": "Rahul is arriving at Kolkata Airport (T2) and needs a cab",
                "sender": "Rahul",
                "timestamp": "Yesterday 8:30 PM",
                "category": "travel",
                "urgent": True,
            },
        ],
        "audio_path": str(_SAMPLE_AUDIO),
        "audio_url": "/audio/sample_demo",
    }
}
_MEMORY_LEADERBOARD: Dict[str, Any] = {
    "saaras": {
        "avg_wer_monolingual": 0.1481,
        "avg_llm_judge_codemixed": 4.8,
        "avg_latency_ms": 120,
        "noise_hallucinations": 0,
    },
    "whisper": {
        "avg_wer_monolingual": 0.1481,
        "avg_llm_judge_codemixed": 4.8,
        "avg_latency_ms": 95,
        "noise_hallucinations": 1,
    },
}


class Database:
    def __init__(self):
        self._clients: Dict[Any, motor.motor_asyncio.AsyncIOMotorClient] = {}

    @property
    def uri(self) -> str:
        return os.getenv("MONGODB_URI", "")

    @property
    def db_name(self) -> str:
        return os.getenv("MONGODB_DB_NAME", "amar_khobor")

    def _get_db(self):
        uri = self.uri
        if not uri or ("mongodb+srv://" not in uri and "mongodb://" not in uri):
            return None

        # Offline mode never touches the network; in-memory/disk fallbacks are used instead.
        if settings.MOCK_MODE:
            return None

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None

        if loop not in self._clients:
            try:
                self._clients[loop] = motor.motor_asyncio.AsyncIOMotorClient(
                    uri,
                    serverSelectionTimeoutMS=1500,
                )
            except Exception:
                return None

        return self._clients[loop][self.db_name]

    async def save_digest(self, digest: Dict[str, Any]) -> None:
        if "created_at" not in digest:
            digest["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Update in-memory cache with bounded size (cap at 50 to prevent memory growth)
        _MEMORY_DIGESTS[digest["id"]] = digest
        if len(_MEMORY_DIGESTS) > 50:
            oldest_key = next(iter(_MEMORY_DIGESTS))
            _MEMORY_DIGESTS.pop(oldest_key, None)

        db = self._get_db()
        if db is not None:
            try:
                doc = dict(digest)
                doc["_id"] = digest["id"]
                await db.digests.replace_one({"_id": digest["id"]}, doc, upsert=True)
            except (PyMongoError, Exception):
                pass

    async def get_digest(self, digest_id: str) -> Optional[Dict[str, Any]]:
        db = self._get_db()
        if db is not None:
            try:
                doc = await db.digests.find_one({"_id": digest_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except (PyMongoError, Exception):
                pass

        return _MEMORY_DIGESTS.get(digest_id)

    async def list_digests(self, limit: int = 50) -> List[Dict[str, Any]]:
        db = self._get_db()
        if db is not None:
            try:
                cursor = db.digests.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
                items = await cursor.to_list(length=limit)
                if items:
                    return items
            except (PyMongoError, Exception):
                pass

        items = list(_MEMORY_DIGESTS.values())
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[:limit]

    async def save_leaderboard(self, data: Dict[str, Any]) -> None:
        _MEMORY_LEADERBOARD.update(data)
        db = self._get_db()
        if db is not None:
            try:
                doc = {
                    "_id": "current_leaderboard",
                    "data": data,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                await db.leaderboard.replace_one({"_id": "current_leaderboard"}, doc, upsert=True)
            except (PyMongoError, Exception):
                pass

    async def get_leaderboard(self) -> Dict[str, Any]:
        db = self._get_db()
        if db is not None:
            try:
                doc = await db.leaderboard.find_one({"_id": "current_leaderboard"})
                if doc and "data" in doc:
                    return doc["data"]
            except (PyMongoError, Exception):
                pass

        # Check disk benchmark results from CLI run (python -m pipeline.eval)
        eval_path = Path("test_data/eval_results.json")
        if eval_path.exists():
            try:
                return json.loads(eval_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        return _MEMORY_LEADERBOARD


db = Database()
