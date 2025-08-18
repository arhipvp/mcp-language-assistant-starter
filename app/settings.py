"""Application configuration loading and validation."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def require_env(keys: list[str]) -> None:
    """Ensure that all ``keys`` are present in the environment.

    Raises
    ------
    RuntimeError
        If any of the required keys are missing.
    """
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


@dataclass(frozen=True)
class Settings:
    OPENROUTER_API_KEY: str
    OPENROUTER_TEXT_MODEL: str
    OPENROUTER_IMAGE_MODEL: str
    ANKI_CONNECT_URL: str
    ANKI_DECK: str
    TELEGRAM_BOT_TOKEN: str
    ANKI_TAG: str = "tg-auto"


def _load() -> Settings:
    require_env(
        [
            "OPENROUTER_API_KEY",
            "OPENROUTER_TEXT_MODEL",
            "OPENROUTER_IMAGE_MODEL",
            "ANKI_DECK",
            "TELEGRAM_BOT_TOKEN",
        ]
    )
    settings = Settings(
        OPENROUTER_API_KEY=os.environ["OPENROUTER_API_KEY"],
        OPENROUTER_TEXT_MODEL=os.environ["OPENROUTER_TEXT_MODEL"],
        OPENROUTER_IMAGE_MODEL=os.environ["OPENROUTER_IMAGE_MODEL"],
        ANKI_CONNECT_URL=os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765"),
        ANKI_DECK=os.environ["ANKI_DECK"],
        TELEGRAM_BOT_TOKEN=os.environ["TELEGRAM_BOT_TOKEN"],
        ANKI_TAG=os.getenv("ANKI_TAG", "tg-auto"),
    )
    _log_config(settings)
    return settings


def _log_config(cfg: Settings) -> None:
    logger.info("OPENROUTER_API_KEY: %s", "set" if cfg.OPENROUTER_API_KEY else "not set")
    logger.info("OPENROUTER_TEXT_MODEL: %s", cfg.OPENROUTER_TEXT_MODEL)
    logger.info("OPENROUTER_IMAGE_MODEL: %s", cfg.OPENROUTER_IMAGE_MODEL)
    logger.info("ANKI_CONNECT_URL: %s", cfg.ANKI_CONNECT_URL)
    logger.info("ANKI_DECK: %s", cfg.ANKI_DECK)
    logger.info("ANKI_TAG: %s", cfg.ANKI_TAG)
    logger.info(
        "TELEGRAM_BOT_TOKEN: %s",
        "set" if cfg.TELEGRAM_BOT_TOKEN else "not set",
    )


settings = _load()
