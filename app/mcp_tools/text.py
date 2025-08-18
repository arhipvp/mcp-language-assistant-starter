"""Text-related MCP tools."""
from __future__ import annotations

from typing import Any, Dict, List

# llm_text is expected to be provided by the environment.
try:  # pragma: no cover - optional dependency
    from . import llm_text  # type: ignore
except Exception:  # pragma: no cover
    llm_text = None  # type: ignore

SYSTEM_PROMPT = (
    "Write one short, natural German B1 sentence (6–12 words) "
    "that MUST include the target word. No quotes."
)


def _extract_content(resp: Any) -> str:
    """Extract text content from an llm_text.chat response."""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        # common response shapes
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


def generate_sentence(word_de: str) -> str:
    """Generate a B1-level German sentence containing ``word_de``."""
    if llm_text is None:
        raise RuntimeError("llm_text provider is not configured")

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": word_de},
    ]
    resp = llm_text.chat(messages)
    text = _extract_content(resp)
    # remove quotes and extra spaces
    text = text.replace("\"", "").replace("'", "")
    text = " ".join(text.split()).strip()
    return text
