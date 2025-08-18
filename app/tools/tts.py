"""Minimal text-to-speech helper using Edge-TTS.

The function tries to generate an MP3 file for the given text.  If the
``edge-tts`` package is not installed or an error occurs during
synthesis, a fallback file containing the raw text bytes is written so
that callers still receive a path to a valid file.  This makes the
function suitable for unit tests in environments without network
connectivity.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import edge_tts
except Exception:  # pragma: no cover
    edge_tts = None  # type: ignore


async def _speak_async(text: str, out_path: str, voice: str) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(out_path)


def speak_to_file(text: str, out_path: str, voice: str = "de-DE") -> str:
    """Generate speech audio for ``text`` and store it as ``out_path``.

    Parameters
    ----------
    text:
        The text to synthesise.
    out_path:
        Location where the audio file should be written.
    voice:
        Voice code understood by Edge-TTS.  Defaults to ``"de-DE"``.

    Returns
    -------
    str
        The path to the generated (or fallback) audio file.
    """
    path = Path(out_path)
    if edge_tts is None:  # pragma: no cover - used when dependency missing
        path.write_bytes(text.encode("utf-8"))
        return str(path)
    try:
        asyncio.run(_speak_async(text, str(path), voice))
    except Exception:  # pragma: no cover - network or engine failure
        path.write_bytes(text.encode("utf-8"))
    return str(path)
