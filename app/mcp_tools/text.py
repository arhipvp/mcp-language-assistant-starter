from __future__ import annotations

"""Simple text utilities backed by a chat-based LLM."""

from typing import Any, Dict, List

from . import llm_text


def translate_text(text: str, src: str, tgt: str) -> str:
    """Translate ``text`` to ``tgt`` using a chat LLM.

    Parameters
    ----------
    text:
        The input string to translate.
    src:
        Source language code.  Currently unused but kept for symmetry
        with potential future extensions.
    tgt:
        Target language code.
    """
    if llm_text is None:  # pragma: no cover - runtime configuration issue
        raise RuntimeError("llm_text client is not configured")

    system_instruction = f"Translate to {tgt}. Output only the translation."
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": text},
    ]
    response = llm_text.chat(messages=messages)

    # Many LLM SDKs return either a plain string or objects with a
    # ``content``/``choices`` field.  Handle the common variants.
    if isinstance(response, str):
        return response.strip()

    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ]
        return "".join(parts).strip()

    choices = getattr(response, "choices", None)
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if isinstance(message, dict):
            content = message.get("content", "")
        else:
            content = getattr(message, "content", "")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content).strip()

    return str(response).strip()
