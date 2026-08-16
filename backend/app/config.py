"""
Centralised application configuration loaded from environment variables / .env file.
All other modules import from here — never from os.environ directly.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Mistral AI — console.mistral.ai (free plan, no card) ─────────────────
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "mistral-small-latest"
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"

    # ── Google Gemini — aistudio.google.com/apikey (1500 req/day free) ───────
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # ── OpenRouter — openrouter.ai (free :free models) ───────────────────────
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── Performance ───────────────────────────────────────────────────────────
    LLM_TIMEOUT: int = 30

    # ── File Upload ───────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60


settings = Settings()
