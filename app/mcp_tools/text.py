"""Text-related MCP tools."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from app.net.http import NetworkError, request_json

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


def _chat_openrouter(messages: List[dict]) -> Dict[str, Any]:
    """Fallback chat via OpenRouter using our generic JSON client."""
    api_key = settings.OPENROUTER_API_KEY
    model = settings.OPENROUTER_TEXT_MODEL
    missing = []
    if not api_key:
        missing.append("OPENROUTER_API_KEY")
    if not model:
        missing.append("OPENROUTER_TEXT_MODEL")
    if missing:
        raise NetworkError("config", "OpenRouter is not configured", {"missing": missing})

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": messages}

    # keep the call local and reusable; _chat() will extract text content
    return request_json("POST", CHAT_URL, headers=headers, json=payload, timeout=30)


def _chat(messages: List[dict]) -> str:
    """Unified chat: prefer local llm_text, else OpenRouter fallback."""
    if llm_text is not None:
        resp = llm_text.chat(messages)  # type: ignore[attr-defined]
    else:
        resp = _chat_openrouter(messages)
    return _extract_content(resp).strip()


def _clean_line(text: str) -> str:
    # remove quotes and normalize whitespace
    text = text.replace('"', "").replace("'", "")
    return " ".join(text.split()).strip()


def _includes_target(word_de: str, sentence_de: str) -> bool:
    """Return True if `sentence_de` contains `word_de` (normalized)."""

    def _norm(s: str) -> str:
        s = s.lower()
        s = s.translate(
            str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss"})
        )
        s = re.sub(r"[^\w\s]", "", s)
        return s

    word = _norm(word_de)
    sent = _norm(sentence_de)
    return re.search(rf"\b{re.escape(word)}\b", sent) is not None


# ── public API ────────────────────────────────────────────────────────────────
def generate_sentence(word_de: str) -> str:
    """Generate a single B1-level German sentence containing `word_de`."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": word_de},
    ]
    last: str = ""
    for _ in range(3):
        out = _chat(messages)
        cleaned = _clean_line(out)
        if _includes_target(word_de, cleaned):
            return cleaned
        last = cleaned
    raise NetworkError("validation", "target word missing", {"word": word_de, "sentence": last})


def translate_text(text: str, src: str, tgt: str) -> str:
    """Translate `text` from `src` to `tgt` (e.g., 'de'↔'ru'). Returns translation only."""
    messages = [
        {"role": "system", "content": f"Translate to {tgt}. Output only the translation."},
        {"role": "user", "content": text},
    ]
    out = _chat(messages)
    return _clean_line(out)
