"""Simple wrapper around OpenRouter chat completions."""
from __future__ import annotations

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

from app.net.http import NetworkError, request_json

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise NetworkError("config", f"Environment variable {key} is not set")
    return value


def chat(
    messages: List[Dict],
    model: Optional[str] = None,
    max_tokens: int = 200,
) -> str:
    """Call OpenRouter chat completions API.

    Args:
        messages: Conversation messages in OpenAI format.
        model: Model name; defaults to ``OPENROUTER_TEXT_MODEL`` env var.
        max_tokens: Maximum tokens for completion.

    Returns:
        The generated text from the first choice.

    Raises:
        NetworkError: If configuration is missing or the request fails.
    """

    api_key = _get_env("OPENROUTER_API_KEY")
    if model is None:
        model = _get_env("OPENROUTER_TEXT_MODEL")

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "max_tokens": max_tokens, "messages": messages}

    data = request_json("POST", API_URL, json=payload, headers=headers, timeout=20)
    return data["choices"][0]["message"]["content"]
