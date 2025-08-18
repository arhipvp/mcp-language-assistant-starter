from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from app.net.http import request_json

# --- env / config ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_IMAGE_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL", "")
IMAGES_URL = "https://openrouter.ai/api/v1/images"

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)


def _build_prompt(sentence_de: str) -> str:
    # более надёжный промпт: рисуем смысл, без текста
    return (
        "Illustrate the meaning of this simple German sentence without any text: "
        f"{sentence_de}"
    )


def generate_image_file(sentence_de: str) -> str:
    """Generate and save an image (PNG) that illustrates a simple German sentence.

    Reads OPENROUTER_API_KEY and OPENROUTER_IMAGE_MODEL from environment (.env supported).
    Returns absolute/relative file path on success, or an empty string on failure.
    """
    if not OPENROUTER_API_KEY or not OPENROUTER_IMAGE_MODEL:
        return ""

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload: dict[str, Any] = {
        "model": OPENROUTER_IMAGE_MODEL,
        "prompt": _build_prompt(sentence_de),
    }

    try:
        data = request_json("POST", IMAGES_URL, headers=headers, json=payload, timeout=60).get(
            "data"
        )
        if not data:
            raise ValueError("Empty data from image API")

        item = data[0]
        # предпочтительно b64_json, но поддержим и прямую ссылку
        if "b64_json" in item and item["b64_json"]:
            img_bytes = base64.b64decode(item["b64_json"])
        elif "url" in item and item["url"]:
            img_resp = requests.get(item["url"], timeout=60)
            img_resp.raise_for_status()
            img_bytes = img_resp.content
        else:
            raise ValueError("No image payload (b64_json/url) in response")

        # стабильное имя + защита от коллизий
        timestamp = int(time.time())
        safe_hash = abs(hash(sentence_de)) % (10**12)
        out_path = MEDIA_DIR / f"img_{safe_hash}_{timestamp}.png"
        out_path.write_bytes(img_bytes)
        return str(out_path)
    except Exception:
        return ""
