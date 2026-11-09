"""Application settings, read from environment variables / backend/.env."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# backend/.env  (this file is backend/app/core/config.py)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass
class Settings:

    # --- AI model ---
    groq_api_key: str | None = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY")
    )
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    )
    llm_timeout_seconds: float = field(
        default_factory=lambda: _float("LLM_TIMEOUT_SECONDS", 30.0)
    )
    llm_max_retries: int = field(
        default_factory=lambda: _int("LLM_MAX_RETRIES", 2)
    )

    # --- Uploads ---
    max_upload_mb: int = field(default_factory=lambda: _int("MAX_UPLOAD_MB", 5))
    max_pdf_pages: int = field(default_factory=lambda: _int("MAX_PDF_PAGES", 15))
    # Resume text longer than this is cut before it is sent to the AI
    max_resume_chars: int = field(
        default_factory=lambda: _int("MAX_RESUME_CHARS", 20000)
    )

    # --- Browser access (the React frontend runs on Vite's port 5173) ---
    cors_origins: list[str] = field(default_factory=_origins)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
