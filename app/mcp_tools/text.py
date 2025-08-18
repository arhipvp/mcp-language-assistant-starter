"""Text-related MCP tools."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# ── optional local provider (preferred if present) ────────────────────────────
try:  # pragma: no cover - optional dependency
    from . import llm_text  # type: ignore
except Exception:  # pragma: no cover
    llm_text = None  # type: ignore

# ── env / config for OpenRouter fallback ─────────────────────────────────────
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_TEXT_MODEL = os.getenv("OPENROUTER_TEXT_MODEL", "")
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
    return str(resp)


def _chat_openrouter(messages: List[dict]) -> str:
    """Fallback chat via OpenRouter with retries."""
    if not OPENROUTER_API_KEY or not OPENROUTER_TEXT_MODEL:
        raise RuntimeError("OpenRouter is not configured (OPENROUTER_API_KEY/TEXT_MODEL).")

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {"model": OPENROUTER_TEXT_MODEL, "messages": messages}

    for attempt in range(3):
        try:
            resp = requests.post(CHAT_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return _extract_content(data)
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
    """Translate `text` from `src` to `tgt` (e.g., 'de'↔'ru')."""
    # Keep system brief to avoid explanations
    messages = [
        {"role": "system", "content": "You are a precise DE↔RU translation assistant. Reply with translation only."},
        {"role": "user", "content": f"Translate from {src} to {tgt}: {text}"},
    ]
    out = _chat(messages)
    return _clean_line(out)
