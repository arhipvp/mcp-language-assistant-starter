"""Application configuration loaded from environment."""
from __future__ import annotations

import os
import logging

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator

load_dotenv()


class Settings(BaseModel):
    """Central application settings."""

    OPENROUTER_API_KEY: str
    OPENROUTER_TEXT_MODEL: str
    ANKI_CONNECT_URL: str = "http://127.0.0.1:8765"
    ANKI_DECK: str
    ANKI_TAG: str = "tg-auto"
    TELEGRAM_BOT_TOKEN: str
    TEXT_MAX_RETRIES: int = 3
    IMAGE_MAX_RETRIES: int = 3
    GENERATION_DELAY_MS: int = 0

    # GenAPI image settings
    GENAPI_API_KEY: str = ""
    GENAPI_MODEL_ID: str = "gpt-image-1"
    GENAPI_SIZE: str = "1024x1024"
    GENAPI_QUALITY: str = "low"
    GENAPI_OUTPUT_FORMAT: str = "png"
    GENAPI_IS_SYNC: bool = True
    GENAPI_CALLBACK_URL: str | None = None

    @field_validator("GENAPI_QUALITY", mode="before")
    @classmethod
    def _validate_quality(cls, v: str | None) -> str:
        v = (v or "low").lower()
        if v not in {"low", "medium", "high"}:
            raise ValueError("GENAPI_QUALITY must be one of: low, medium, high")
        return v


def _load_settings() -> Settings:
    try:
        data = {
            "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
            "OPENROUTER_TEXT_MODEL": os.environ["OPENROUTER_TEXT_MODEL"],
            "ANKI_CONNECT_URL": os.environ.get("ANKI_CONNECT_URL", "http://127.0.0.1:8765"),
            "ANKI_DECK": os.environ["ANKI_DECK"],
            "ANKI_TAG": os.environ.get("ANKI_TAG", "tg-auto"),
            "TELEGRAM_BOT_TOKEN": os.environ["TELEGRAM_BOT_TOKEN"],
            "TEXT_MAX_RETRIES": int(os.environ.get("TEXT_MAX_RETRIES", 3)),
            "IMAGE_MAX_RETRIES": int(os.environ.get("IMAGE_MAX_RETRIES", 3)),
            "GENERATION_DELAY_MS": int(os.environ.get("GENERATION_DELAY_MS", 0)),
            "GENAPI_API_KEY": os.environ.get("GENAPI_API_KEY", ""),
            "GENAPI_MODEL_ID": os.environ.get("GENAPI_MODEL_ID", "gpt-image-1"),
            "GENAPI_SIZE": os.environ.get("GENAPI_SIZE", "1024x1024"),
            "GENAPI_QUALITY": os.environ.get("GENAPI_QUALITY", "low"),
            "GENAPI_OUTPUT_FORMAT": os.environ.get("GENAPI_OUTPUT_FORMAT", "png"),
            "GENAPI_IS_SYNC": os.environ.get("GENAPI_IS_SYNC", "true").lower()
            in {"1", "true", "yes"},
            "GENAPI_CALLBACK_URL": os.environ.get("GENAPI_CALLBACK_URL") or None,
        }
    except KeyError as e:  # pragma: no cover - simple error path
        raise RuntimeError(f"Missing required environment variable: {e.args[0]}") from None

    try:
        return Settings(**data)
    except ValidationError as exc:  # pragma: no cover - simple validation error
        raise RuntimeError(str(exc)) from None


settings = _load_settings()


def log_effective_settings(logger: logging.Logger) -> None:
    """Вывести ключевые настройки приложения без секретов."""

    logger.info(
        "text_model=%s genapi_model=%s anki_url=%s deck=\"%s\" tag=\"%s\" retries=%s/%s",
        settings.OPENROUTER_TEXT_MODEL,
        settings.GENAPI_MODEL_ID,
        settings.ANKI_CONNECT_URL,
        settings.ANKI_DECK,
        settings.ANKI_TAG,
        settings.TEXT_MAX_RETRIES,
        settings.IMAGE_MAX_RETRIES,
    )
