"""Amar Khobor pipeline package.

Bootstrap the .env file into os.environ once, so the CLI, the FastAPI server,
and every provider read the same configuration. Pydantic only reads .env into
its Settings object; without this, os.getenv() in providers returns None.
"""

import os

from dotenv import load_dotenv

load_dotenv(override=False)


def is_mock_mode() -> bool:
    """Single source of truth for offline mode. Defaults to offline (no credits)."""
    return os.getenv("MOCK_MODE", "true").strip().lower() == "true"


def require_key(env_var: str, provider: str) -> str:
    """Return a live API key or fail loudly instead of silently mocking."""
    key = os.getenv(env_var, "").strip()
    if not key:
        raise RuntimeError(
            f"{provider} is in live mode but {env_var} is empty. "
            f"Set it in .env, or set MOCK_MODE=true to run offline."
        )
    return key
