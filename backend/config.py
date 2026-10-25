import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # STT Providers
    SARVAM_API_KEY: str = ""
    SARVAM_API_URL: str = "https://api.sarvam.ai/speech-to-text"
    SARVAM_MODEL: str = "saaras:v4"

    GROQ_API_KEY: str = ""
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/audio/transcriptions"
    WHISPER_MODEL: str = "whisper-large-v3"

    STT_PROVIDER: str = "saaras"

    # LLM & Gemma (Summarizer & Bake-Off LLM-Judge)
    GEMINI_API_KEY: str = ""
    GEMMA_MODEL: str = "gemma-4"
    LLM_API_URL: str = ""  # Optional custom base URL (e.g. for Groq or OpenAI-compatible endpoint)
    LLM_PROVIDER: str = "google"  # "google", "groq", or "openai_compatible"

    # TTS (model is selected via ELEVENLABS_MODEL_ID)
    TTS_ENGINE: str = "edge-tts"
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_API_URL: str = "https://api.elevenlabs.io/v1/text-to-speech"
    ELEVENLABS_MODEL_ID: str = "eleven_v4_turbo"
    ELEVENLABS_VOICE_ID: str = "Y8AULI9gwzMzFX41r7IP"
    EDGE_TTS_VOICE: str = "bn-IN-BashkarNeural"

    # Database (MongoDB Atlas)
    MONGODB_URI: str = "mongodb://localhost:27017/amar_khobor"
    MONGODB_DB_NAME: str = "amar_khobor"

    # Testing & Offline Operations
    MOCK_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
