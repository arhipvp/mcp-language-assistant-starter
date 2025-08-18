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
        }
    except KeyError as e:  # pragma: no cover - simple error path
        raise RuntimeError(f"Missing required environment variable: {e.args[0]}") from None

    try:
        return Settings(**data)
    except ValidationError as exc:  # pragma: no cover - simple validation error
        raise RuntimeError(str(exc)) from None


settings = _load_settings()
