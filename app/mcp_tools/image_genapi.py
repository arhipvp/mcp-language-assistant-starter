from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import requests
from app.settings import settings

# external client functions; they will be patched in tests
try:  # pragma: no cover - optional dependency
    from genapi import create_generation_task, get_task_status  # type: ignore
except Exception:  # pragma: no cover - library may be absent
    create_generation_task = None  # type: ignore
    get_task_status = None  # type: ignore

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

_EXT_TO_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _guess_mime_from_bytes(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    return None


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


def generate_image_file_genapi(
    sentence_de: str,
    ref_image: str | bytes | None = None,
    ref_kind: str | None = None,
) -> str:
    """
    Generate an image via GenAPI. Return local file path or empty string.

    Parameters
    ----------
    ref_image:
        - str: local path or http(s) URL
        - bytes: file content (will be encoded to base64)
        - None: no reference
    ref_kind: optional hint to force type ('path' | 'url' | 'b64')
    """

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

    quality = settings.GENAPI_QUALITY
    kwargs: Dict[str, Any] = {
        "model_id": model_id,
        "prompt": prompt,
        "is_sync": is_sync,
        "quality": quality,
    }
    if callback_url:
        kwargs["callback_url"] = callback_url
    logger.info("image.gen: model=%s quality=%s", model_id, quality)

    # reference image handling
    ref_payload: Dict[str, str] = {}
    if ref_image is not None:
        allowed_types = {
            t.strip() for t in os.environ.get("GENAPI_ALLOWED_IMAGE_TYPES", "").split(",") if t.strip()
        }
        max_bytes = _env_int("GENAPI_REF_IMAGE_MAX_BYTES", 0)

        kind = ref_kind
        if isinstance(ref_image, str) and not kind:
            if ref_image.startswith("http://") or ref_image.startswith("https://"):
                kind = "url"
            elif os.path.isfile(ref_image):
                kind = "path"
        if isinstance(ref_image, bytes):
            kind = "b64"

        if kind == "url" and isinstance(ref_image, str):
            ref_payload["image_url"] = ref_image
        elif kind == "path" and isinstance(ref_image, str):
            if not os.path.isfile(ref_image):
                logger.warning("Reference image path not found: %s", ref_image)
            else:
                size = os.path.getsize(ref_image)
                if max_bytes and size > max_bytes:
                    logger.warning("Reference image too large: %s", size)
                    return ""
                mime = _EXT_TO_MIME.get(Path(ref_image).suffix.lower())
                if allowed_types and mime not in allowed_types:
                    # try signature for better guess
                    try:
                        with open(ref_image, "rb") as fh:
                            mime = _guess_mime_from_bytes(fh.read(8))
                    except Exception:
                        mime = None
                if allowed_types and mime not in allowed_types:
                    logger.warning("Unsupported reference image type: %s", mime)
                    return ""
                ref_payload["image_path"] = ref_image
        elif kind == "b64":
            data = ref_image if isinstance(ref_image, bytes) else base64.b64decode(ref_image)
            size = len(data)
            if max_bytes and size > max_bytes:
                logger.warning("Reference image too large: %s", size)
                return ""
            mime = _guess_mime_from_bytes(data)
            if allowed_types and mime not in allowed_types:
                logger.warning("Unsupported reference image type: %s", mime)
                return ""
            ref_payload["image_b64"] = base64.b64encode(data).decode()
        else:
            logger.warning("Unsupported reference image input")

    kwargs.update(ref_payload)

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
