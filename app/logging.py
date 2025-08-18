from __future__ import annotations

import logging
from logging.config import dictConfig
import os
from pathlib import Path
import re
from typing import Iterable

from dotenv import load_dotenv


class ContextFilter(logging.Filter):
    """Добавляет недостающие поля trace/run/step."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        if not hasattr(record, "trace_id"):
            record.trace_id = "-"
        if not hasattr(record, "run_id"):
            record.run_id = "-"
        if not hasattr(record, "step"):
            record.step = "-"
        return True


class SecretsFilter(logging.Filter):
    """Маскирует известные секреты в сообщениях логов."""

    def __init__(self, secrets: Iterable[str]) -> None:  # pragma: no cover - simple
        super().__init__()
        escaped = [re.escape(s) for s in secrets if s]
        self._regex = re.compile("|".join(escaped)) if escaped else None

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple
        def _mask(value: object) -> object:
            if isinstance(value, str) and self._regex:
                return self._regex.sub("***", value)
            return value

        record.msg = _mask(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_mask(a) for a in record.args)
        elif isinstance(record.args, dict):
            record.args = {k: _mask(v) for k, v in record.args.items()}
        return True


_configured = False


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure root logger with console and rotating file handlers."""

    global _configured
    if _configured:
        return logging.getLogger()

    load_dotenv()
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    Path(os.path.dirname(log_file)).mkdir(parents=True, exist_ok=True)

    secrets = [
        v
        for k, v in os.environ.items()
        if any(key in k for key in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
    ]

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s trace=%(trace_id)s run=%(run_id)s step=%(step)s %(message)s"
                }
            },
            "filters": {
                "context": {"()": ContextFilter},
                "mask": {"()": SecretsFilter, "secrets": secrets},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level_name,
                    "formatter": "standard",
                    "filters": ["context", "mask"],
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": level_name,
                    "formatter": "standard",
                    "filters": ["context", "mask"],
                    "filename": log_file,
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 5,
                },
            },
            "root": {"level": level_name, "handlers": ["console", "file"]},
        }
    )

    _configured = True
    root = logging.getLogger()
    handlers = ",".join(h.__class__.__name__ for h in root.handlers)
    root.info("logging initialized level=%s handlers=%s", level_name, handlers)
    return root
