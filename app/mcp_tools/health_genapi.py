"""Health check for GenAPI."""

from __future__ import annotations

import logging
from typing import Any, Dict

import requests

from app.settings import settings

IMAGES_URL = "https://api.gen-api.ru/v1/images/generate"

logger = logging.getLogger(__name__)


def genapi_check() -> Dict[str, Any]:
    """Perform a minimal GenAPI request to verify availability."""

    headers = {
        "Authorization": f"Bearer {settings.GENAPI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GENAPI_MODEL_ID,
        "prompt": "test",
        "size": settings.GENAPI_SIZE,
        "quality": settings.GENAPI_QUALITY,
        "background": settings.GENAPI_BACKGROUND,
        "response_format": "b64_json",
        "n": 1,
    }

    try:
        resp = requests.post(IMAGES_URL, headers=headers, json=payload, timeout=10)
    except Exception as exc:
        logger.error("genapi.check error: %s", exc)
        return {"ok": False, "error": str(exc)}

    if resp.status_code != 200:
        snippet = resp.text[:200]
        logger.error("genapi.check error: HTTP %s %s", resp.status_code, snippet)
        return {"ok": False, "status": resp.status_code, "body": snippet}

    try:
        data = resp.json()
    except Exception:
        snippet = resp.text[:200]
        logger.error("genapi.check error: non-JSON %s", snippet)
        return {"ok": False, "status": resp.status_code, "body": snippet}

    request_id = data.get("id") or data.get("request_id")
    logger.info("genapi.check ok: %s", request_id)
    return {"ok": True, "id": request_id}

