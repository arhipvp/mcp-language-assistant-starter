from __future__ import annotations

"""Simple health checks for external integrations."""

from typing import Any, Dict

from app.net.http import NetworkError, request_json
from app.settings import settings


def _check_openrouter(model: str) -> Dict[str, Any]:
    """Validate that API key and model look sane."""

    api_key = settings.OPENROUTER_API_KEY
    if not api_key or not api_key.startswith("sk-"):
        return {"ok": False, "model": None, "error": "invalid OPENROUTER_API_KEY"}

    if not model:
        return {"ok": False, "model": None, "error": "missing model"}

    return {"ok": True, "model": model, "error": None}


def _check_anki() -> Dict[str, Any]:
    """Call AnkiConnect version endpoint."""

    payload = {"action": "version", "version": 6}
    try:
        request_json("POST", settings.ANKI_CONNECT_URL, json=payload, timeout=5)
    except NetworkError as exc:  # pragma: no cover - handled in tests
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "error": None}


def check_health() -> Dict[str, Dict[str, Any]]:
    """Return health information for integrations."""

    return {
        "openrouter_text": _check_openrouter(settings.OPENROUTER_TEXT_MODEL),
        "anki": _check_anki(),
    }

