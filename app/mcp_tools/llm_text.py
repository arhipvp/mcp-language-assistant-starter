"""Simple wrapper around OpenRouter chat completions."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.net.http import NetworkError, request_json
from app.settings import settings

API_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(
    messages: List[Dict],
    model: Optional[str] = None,
    max_tokens: int = 200,
) -> str:
    """Call OpenRouter chat completions API.

    Args:
        messages: Conversation messages in OpenAI format.
        model: Model name; defaults to settings.OPENROUTER_TEXT_MODEL.
        max_tokens: Maximum tokens for completion.

    Returns:
        The generated text from the first choice.

    Raises:
        NetworkError: If configuration is missing or the request fails.
    """
    api_key = settings.OPENROUTER_API_KEY
    mdl = model or settings.OPENROUTER_TEXT_MODEL

    if not api_key:
        raise NetworkError("config", "OPENROUTER_API_KEY is not set")
    if not mdl:
        raise NetworkError("config", "OPENROUTER_TEXT_MODEL is not set")

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": mdl, "max_tokens": max_tokens, "messages": messages}

    data = request_json("POST", API_URL, json=payload, headers=headers, timeout=20)
    return data["choices"][0]["message"]["content"]
