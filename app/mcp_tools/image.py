from __future__ import annotations

import base64
import hashlib
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

from app.net.http import request_json
from app.settings import settings

IMAGES_URL = "https://openrouter.ai/api/v1/images"

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


class ImageMeta(Dict[str, str]):
    """Путь к файлу с метаданными, совместимый с os.PathLike."""

    def __init__(self, path: str, hash_: str, model: str) -> None:
        super().__init__(path=path, hash=hash_, model=model)

    def __fspath__(self) -> str:  # type: ignore[override]
        return self["path"]

    def __str__(self) -> str:  # type: ignore[override]
        return self["path"]


def _build_prompt(sentence_de: str) -> str:
    # более надёжный промпт: рисуем смысл, без текста
    return (
        "Illustrate the meaning of this simple German sentence without any text: "
        f"{sentence_de}"
    )


def generate_image_file(sentence_de: str) -> ImageMeta | str:
    """Generate and save an image (PNG) illustrating a German sentence.

    On success returns :class:`ImageMeta` with deterministic name and metadata.
    On any failure returns an empty string.
    """
    logger.info("start", extra={"step": "image.generate"})
    start = time.perf_counter()
    model = settings.OPENROUTER_IMAGE_MODEL
    if not settings.OPENROUTER_API_KEY or not model:
        logger.warning("skip", extra={"step": "image.generate"})
        return ""

    hash_input = f"{sentence_de}{model}".encode("utf-8")
    hash_hex = hashlib.sha1(hash_input).hexdigest()
    out_path = MEDIA_DIR / f"img_{hash_hex}.png"

    if out_path.exists():
        lat_ms = int((time.perf_counter() - start) * 1000)
        logger.info("ok", extra={"step": "image.generate", "lat_ms": lat_ms, "outlen": 0})
        return ImageMeta(str(out_path), hash_hex, model)

    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
    payload: dict[str, Any] = {"model": model, "prompt": _build_prompt(sentence_de)}

    try:
        data = request_json(
            "POST", IMAGES_URL, headers=headers, json=payload, timeout=60
        ).get("data")
        if not data:
            raise ValueError("Empty data from image API")

        item = data[0]
        # предпочтительно б64_json, но поддержим и прямую ссылку
        if "b64_json" in item and item["b64_json"]:
            img_bytes = base64.b64decode(item["b64_json"])
        elif "url" in item and item["url"]:
            img_resp = requests.get(item["url"], timeout=60)
            img_resp.raise_for_status()
            img_bytes = img_resp.content
        else:
            raise ValueError("No image payload (b64_json/url) in response")

        out_path.write_bytes(img_bytes)
        lat_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ok",
            extra={"step": "image.generate", "lat_ms": lat_ms, "outlen": len(img_bytes)},
        )
        return ImageMeta(str(out_path), hash_hex, model)
    except Exception:
        logger.error("error", exc_info=True, extra={"step": "image.generate"})
        return ""


def generate_image_file_genapi(sentence_de: str) -> ImageMeta | str:
    """Generate an image using the GenAPI provider.

    This is a placeholder implementation; network calls are expected to be
    mocked in tests. On any failure returns an empty string.
    """
    logger.info("start", extra={"step": "image.generate"})
    logger.warning("skip", extra={"step": "image.generate"})
    return ""
