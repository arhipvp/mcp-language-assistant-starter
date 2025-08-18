"""Text-related MCP tools."""
from __future__ import annotations

import time
from typing import Any, Dict, List

import requests

# ── optional local provider (preferred if present) ────────────────────────────
try:  # pragma: no cover - optional dependency
    from . import llm_text  # type: ignore
except Exception:  # pragma: no cover
    llm_text = None  # type: ignore

# ── env / config for OpenRouter fallback ─────────────────────────────────────
from app.settings import settings

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "Write one short, natural German B1 sentence (6–12 words) "
    "that MUST include the target word. No quotes."
)


# ── helpers ──────────────────────────────────────────────────────────────────
def _extract_content(resp: Any) -> str:
    """Extract text content from a variety of response shapes."""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        if isinstance(resp.get("content"), str):
            return resp["content"]
        if resp.get("choices"):
            choice = resp["choices"][0]
            if isinstance(choice, dict):
                message = choice.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
        if isinstance(resp.get("text"), str):
            return resp["text"]
    # try generic attribute-style SDKs
    content = getattr(resp, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ]
        return "".join(parts)
    choices = getattr(resp, "choices", None)
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if isinstance(message, dict):
            msg_content = message.get("content", "")
        else:
            msg_content = getattr(message, "content", "")
        if isinstance(msg_content, list):
            msg_content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in msg_content
            )
        return str(msg_content)
    return str(resp)


def _chat_openrouter(messages: List[dict]) -> str:
    """Fallback chat via OpenRouter with retries."""
    api_key = settings.OPENROUTER_API_KEY
    model = settings.OPENROUTER_TEXT_MODEL

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": messages}

    for attempt in range(3):
        try:
            resp = requests.post(CHAT_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return _extract_content(data).strip()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Failed to get completion")


def _chat(messages: List[dict]) -> str:
    """Unified chat: prefer local llm_text, else OpenRouter fallback."""
    if llm_text is not None:
        resp = llm_text.chat(messages)  # type: ignore[attr-defined]
        return _extract_content(resp).strip()
    return _chat_openrouter(messages).strip()


def _clean_line(text: str) -> str:
    # remove quotes and normalize whitespace
    text = text.replace('"', "").replace("'", "")
    return " ".join(text.split()).strip()


# ── public API ────────────────────────────────────────────────────────────────
def generate_sentence(word_de: str) -> str:
    """Generate a single B1-level German sentence containing `word_de`."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": word_de},
    ]
    out = _chat(messages)
    return _clean_line(out)


def translate_text(text: str, src: str, tgt: str) -> str:
    """Translate `text` from `src` to `tgt` (e.g., 'de'↔'ru'). Returns translation only."""
    messages = [
        {"role": "system", "content": f"Translate to {tgt}. Output only the translation."},
        {"role": "user", "content": text},
    ]
    out = _chat(messages)
    return _clean_line(out)
