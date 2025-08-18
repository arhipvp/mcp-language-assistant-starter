"""Image generation via GenAPI."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests

from app.settings import settings

IMAGES_URL = "https://api.gen-api.ru/v1/images"

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


def _build_prompt(sentence_de: str) -> str:
    return f"Illustrate the meaning of this German sentence without text: {sentence_de}"


def generate_image_file(sentence_de: str) -> str:
    """Generate image illustrating ``sentence_de`` via GenAPI.

    Returns a relative path like ``media/uuid.png`` or an empty string on any
    error. All errors are logged but never raised.
    """

    logger.info("start", extra={"step": "image.generate"})
    api_key = settings.GENAPI_API_KEY
    if not api_key:
        logger.warning("GENAPI_API_KEY is empty", extra={"step": "image.generate"})
        return ""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": settings.GENAPI_MODEL_ID,
        "prompt": _build_prompt(sentence_de),
        "size": settings.GENAPI_SIZE,
        "quality": settings.GENAPI_QUALITY,
        "output_format": settings.GENAPI_OUTPUT_FORMAT,
        "n": 1,
        "sync": settings.GENAPI_IS_SYNC,
    }
    if settings.GENAPI_CALLBACK_URL is not None:
        payload["callback_url"] = settings.GENAPI_CALLBACK_URL

    try:
        resp = requests.post(IMAGES_URL, headers=headers, json=payload, timeout=60)
    except Exception as exc:
        logger.error("image.generate error: %s", exc)
        return ""

    if not settings.GENAPI_IS_SYNC:
        if resp.status_code == 200:
            logger.info(
                "request sent, result will arrive via callback",
                extra={"step": "image.generate"},
            )
        else:
            logger.error(
                "image.generate error: HTTP %s %s",
                resp.status_code,
                resp.text[:200],
            )
        return ""

    try:
        data = resp.json()
    except Exception:
        logger.error(
            "image.generate error: non-JSON response %s %s",
            resp.status_code,
            resp.text[:200],
        )
        return ""

    try:
        b64 = data["data"][0]["b64_json"]
    except Exception as exc:
        logger.error("image.generate error: %s", exc)
        return ""

    try:
        img_bytes = base64.b64decode(b64)
        filename = f"{uuid4()}.png"
        out_path = MEDIA_DIR / filename
        out_path.write_bytes(img_bytes)
        logger.info("ok", extra={"step": "image.generate", "outlen": len(img_bytes)})
        return str(Path("media") / filename)
    except Exception as exc:
        logger.error("image.generate error: %s", exc)
        return ""

