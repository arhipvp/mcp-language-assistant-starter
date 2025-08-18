from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

import requests


def generate_image_file(sentence_de: str) -> str:
    """Generate an image illustrating a simple German sentence.

    The function uses the OpenRouter image API and returns the path to the
    generated PNG file.  Environment variables ``OPENROUTER_API_KEY`` and
    ``OPENROUTER_IMAGE_MODEL`` must be set.  On any failure the function
    returns an empty string instead of raising an exception.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("OPENROUTER_IMAGE_MODEL")
    if not api_key or not model:
        return ""

    prompt = (
        "Illustrate the meaning of this simple German sentence without any text: "
        f"{sentence_de}"
    )
    headers = {"Authorization": f"Bearer {api_key}"}
    payload: dict[str, Any] = {"model": model, "prompt": prompt}

    media_dir = Path("media")
    media_dir.mkdir(exist_ok=True)

    for _ in range(3):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/images",
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json().get("data")
            if not data:
                continue
            item = data[0]
            timestamp = str(int(time.time()))
            out_path = media_dir / f"{timestamp}.png"
            if "b64_json" in item:
                image_bytes = base64.b64decode(item["b64_json"])
            elif "url" in item:
                img_resp = requests.get(item["url"], timeout=30)
                img_resp.raise_for_status()
                image_bytes = img_resp.content
            else:
                continue
            out_path.write_bytes(image_bytes)
            return str(out_path)
        except Exception:
            continue
    return ""
