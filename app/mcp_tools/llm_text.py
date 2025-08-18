"""Simple wrapper around OpenRouter chat completions."""
from __future__ import annotations

import time
from typing import Dict, List, Optional

import requests

from app.settings import settings

API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(RuntimeError):
    """Raised when interaction with OpenRouter fails."""
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
        OpenRouterError: If configuration is missing or the request fails.
    """

    api_key = settings.OPENROUTER_API_KEY
    if model is None:
        model = settings.OPENROUTER_TEXT_MODEL

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "max_tokens": max_tokens, "messages": messages}

    delays = [0.5, 1, 2]
    for attempt in range(len(delays) + 1):
        try:
            response = requests.post(
                API_URL, json=payload, headers=headers, timeout=20
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            if attempt == len(delays):
                raise OpenRouterError(f"OpenRouter API request failed: {exc}") from None
            time.sleep(delays[attempt])
