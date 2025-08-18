"""Application configuration loaded from environment."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()


class Settings(BaseModel):
    """Central application settings."""

    OPENROUTER_API_KEY: str
    OPENROUTER_TEXT_MODEL: str
    OPENROUTER_IMAGE_MODEL: str
    ANKI_CONNECT_URL: str = "http://127.0.0.1:8765"
    ANKI_DECK: str
    ANKI_TAG: str = "tg-auto"
    TELEGRAM_BOT_TOKEN: str
    TEXT_MAX_RETRIES: int = 3
    IMAGE_MAX_RETRIES: int = 3
    GENERATION_DELAY_MS: int = 0
    GENAPI_API_KEY: str
    GENAPI_MODEL_ID: str = "gpt-image-1"
    GENAPI_BASE_URL: str = "https://api.gen-api.ru"
    GENAPI_IS_SYNC: str = "false"
    GENAPI_POLL_INTERVAL_MS: str = "1200"
    GENAPI_POLL_TIMEOUT_MS: str = "60000"
    GENAPI_CALLBACK_URL: str = ""
    GENAPI_REQUEST_TIMEOUT_S: str = "30"
    GENAPI_MAX_RETRIES: str = "3"
    GENAPI_MAX_IMAGE_BYTES: str = "5242880"
    GENAPI_ALLOWED_IMAGE_TYPES: str = "image/png,image/jpeg,image/webp"


def _load_settings() -> Settings:
    try:
        data = {
            "OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"],
            "OPENROUTER_TEXT_MODEL": os.environ["OPENROUTER_TEXT_MODEL"],
            "OPENROUTER_IMAGE_MODEL": os.environ["OPENROUTER_IMAGE_MODEL"],
            "ANKI_CONNECT_URL": os.environ.get("ANKI_CONNECT_URL", "http://127.0.0.1:8765"),
            "ANKI_DECK": os.environ["ANKI_DECK"],
            "ANKI_TAG": os.environ.get("ANKI_TAG", "tg-auto"),
            "TELEGRAM_BOT_TOKEN": os.environ["TELEGRAM_BOT_TOKEN"],
            "TEXT_MAX_RETRIES": int(os.environ.get("TEXT_MAX_RETRIES", 3)),
            "IMAGE_MAX_RETRIES": int(os.environ.get("IMAGE_MAX_RETRIES", 3)),
            "GENERATION_DELAY_MS": int(os.environ.get("GENERATION_DELAY_MS", 0)),
            "GENAPI_API_KEY": os.environ["GENAPI_API_KEY"],
            "GENAPI_MODEL_ID": os.environ.get("GENAPI_MODEL_ID", "gpt-image-1"),
            "GENAPI_BASE_URL": os.environ.get(
                "GENAPI_BASE_URL", "https://api.gen-api.ru"
            ),
            "GENAPI_IS_SYNC": os.environ.get("GENAPI_IS_SYNC", "false"),
            "GENAPI_POLL_INTERVAL_MS": os.environ.get(
                "GENAPI_POLL_INTERVAL_MS", "1200"
            ),
            "GENAPI_POLL_TIMEOUT_MS": os.environ.get(
                "GENAPI_POLL_TIMEOUT_MS", "60000"
            ),
            "GENAPI_CALLBACK_URL": os.environ.get("GENAPI_CALLBACK_URL", ""),
            "GENAPI_REQUEST_TIMEOUT_S": os.environ.get(
                "GENAPI_REQUEST_TIMEOUT_S", "30"
            ),
            "GENAPI_MAX_RETRIES": os.environ.get("GENAPI_MAX_RETRIES", "3"),
            "GENAPI_MAX_IMAGE_BYTES": os.environ.get(
                "GENAPI_MAX_IMAGE_BYTES", "5242880"
            ),
            "GENAPI_ALLOWED_IMAGE_TYPES": os.environ.get(
                "GENAPI_ALLOWED_IMAGE_TYPES", "image/png,image/jpeg,image/webp"
            ),
        }
    except KeyError as e:  # pragma: no cover - simple error path
        raise RuntimeError(f"Missing required environment variable: {e.args[0]}") from None

    try:
        return Settings(**data)
    except ValidationError as exc:  # pragma: no cover - simple validation error
        raise RuntimeError(str(exc)) from None


settings = _load_settings()
