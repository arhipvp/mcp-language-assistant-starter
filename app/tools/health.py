from __future__ import annotations

import importlib.util
import os
import time
from typing import Dict

import requests
from dotenv import load_dotenv

load_dotenv()

CACHE_TTL = 5.0
_last_result: Dict[str, Dict[str, str]] | None = None
_last_checked = 0.0


def _wrap(status: str, message: str) -> Dict[str, str]:
    return {"status": status, "message": message}


def _check_openrouter(model_env: str) -> Dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv(model_env, "")
    if not api_key or not model:
        return _wrap("err", "missing OPENROUTER_API_KEY or model")
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=5)
        if resp.status_code >= 500:
            return _wrap("err", f"HTTP {resp.status_code}")
        return _wrap("ok", model)
    except Exception as exc:  # pragma: no cover - network failure
        return _wrap("err", str(exc))


def _check_anki() -> Dict[str, str]:
    url = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")
    try:
        resp = requests.post(url, json={"action": "version", "version": 6}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        ver = data.get("result", "")
        return _wrap("ok", str(ver))
    except Exception as exc:  # pragma: no cover - network failure
        return _wrap("err", str(exc))


def _check_tts() -> Dict[str, str]:
    if importlib.util.find_spec("edge_tts") is None:
        return _wrap("skip", "edge-tts not installed")
    return _wrap("ok", "edge-tts")


def check_health() -> Dict[str, Dict[str, str]]:
    global _last_result, _last_checked
    now = time.time()
    if _last_result is not None and now - _last_checked < CACHE_TTL:
        return _last_result

    result = {
        "openrouter_text": _check_openrouter("OPENROUTER_TEXT_MODEL"),
        "openrouter_image": _check_openrouter("OPENROUTER_IMAGE_MODEL"),
        "anki": _check_anki(),
        "tts": _check_tts(),
    }

    _last_result = result
    _last_checked = now
    return result
