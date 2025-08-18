from __future__ import annotations

from typing import List

from app.net.http import NetworkError, request_json
from importlib import reload
import app.settings as app_settings

# Получаем актуальные настройки при каждом импорте модуля
settings = reload(app_settings).settings

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(messages: List[dict], model: str | None = None, max_tokens: int = 200) -> str:
    """Send chat messages to OpenRouter and return the response text."""
    api_key = settings.OPENROUTER_API_KEY
    use_model = model or settings.OPENROUTER_TEXT_MODEL

    missing: list[str] = []
    if not api_key:
        missing.append("OPENROUTER_API_KEY")
    if not use_model:
        missing.append("OPENROUTER_TEXT_MODEL" if model is None else "model")
    if missing:
        raise NetworkError("config", "OpenRouter is not configured", {"missing": missing})

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": use_model, "messages": messages, "max_tokens": max_tokens}

    data = request_json("POST", CHAT_URL, headers=headers, json=payload, timeout=30)
    return data["choices"][0]["message"]["content"]
