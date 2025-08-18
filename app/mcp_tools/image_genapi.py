from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

# external client functions; they will be patched in tests
try:  # pragma: no cover - optional dependency
    from genapi import create_generation_task, get_task_status  # type: ignore
except Exception:  # pragma: no cover - library may be absent
    create_generation_task = None  # type: ignore
    get_task_status = None  # type: ignore

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _extract_image(resp: Any) -> Tuple[str, str] | None:
    """Return (kind, payload) where kind is 'url' or 'b64'."""
    if not isinstance(resp, dict):
        return None
    if "result" in resp and isinstance(resp["result"], dict):
        return _extract_image(resp["result"])
    items: Any = None
    if isinstance(resp.get("images"), list):
        items = resp["images"]
    elif isinstance(resp.get("data"), list):
        items = resp["data"]
    elif isinstance(resp, list):  # type: ignore[unreachable]
        items = resp
    if items:
        first = items[0]
    else:
        first = resp
    if not isinstance(first, dict):
        return None
    url = first.get("url")
    if isinstance(url, str) and url:
        return ("url", url)
    content = first.get("content") or first.get("b64_json")
    if isinstance(content, str) and content:
        return ("b64", content)
    return None


def _get_request_id(resp: Dict[str, Any]) -> str | None:
    for key in ("request_id", "id", "task_id"):
        val = resp.get(key)
        if isinstance(val, (str, int)):
            return str(val)
    return None


def _save_image(kind: str, data: str, out_path: Path) -> str:
    try:
        if kind == "url":
            resp = requests.get(data, timeout=60)
            resp.raise_for_status()
            img_bytes = resp.content
        else:
            img_bytes = base64.b64decode(data)
        out_path.write_bytes(img_bytes)
        return str(out_path)
    except Exception:
        logger.exception("Failed to save image")
        return ""


def generate_image_file_genapi(sentence_de: str) -> str:
    """Generate an image via GenAPI. Return local file path or empty string."""
    model_id = os.environ.get("GENAPI_MODEL_ID")
    if not model_id or create_generation_task is None or get_task_status is None:
        return ""

    is_sync = os.environ.get("GENAPI_IS_SYNC", "false").lower() == "true"
    callback_url = os.environ.get("GENAPI_CALLBACK_URL")
    poll_interval_ms = _env_int("GENAPI_POLL_INTERVAL_MS", 1000)
    poll_timeout_ms = _env_int("GENAPI_POLL_TIMEOUT_MS", 10000)

    hash_hex = hashlib.sha1(f"{sentence_de}{model_id}".encode("utf-8")).hexdigest()
    out_path = MEDIA_DIR / f"img_{hash_hex}.png"
    if out_path.exists():
        return str(out_path)

    prompt = f"Иллюстрируй смысл простого немецкого предложения без текста: {sentence_de}"

    kwargs: Dict[str, Any] = {"model_id": model_id, "prompt": prompt, "is_sync": is_sync}
    if callback_url:
        kwargs["callback_url"] = callback_url

    try:
        resp = create_generation_task(**kwargs)  # type: ignore[misc]
    except Exception:
        logger.exception("create_generation_task failed")
        return ""

    image = _extract_image(resp)
    if image:
        kind, data = image
        return _save_image(kind, data, out_path)

    request_id = _get_request_id(resp)
    if not request_id:
        logger.error("No request_id for polling")
        return ""

    deadline = time.time() + poll_timeout_ms / 1000
    while time.time() < deadline:
        try:
            status = get_task_status(request_id)  # type: ignore[misc]
        except Exception:
            logger.exception("get_task_status failed")
            return ""
        image = _extract_image(status)
        if image:
            kind, data = image
            return _save_image(kind, data, out_path)
        time.sleep(poll_interval_ms / 1000)

    logger.error("Image generation timed out")
    return ""
