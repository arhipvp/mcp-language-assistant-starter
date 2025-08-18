"""Minimal MCP server wiring the language tools together.

The implementation is intentionally lightweight and only depends on the
`anthropic-mcp` package if it is available.  When the SDK is missing the
module still exposes a :func:`list_tools` helper so that downstream code
can introspect the offered capabilities.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List

try:  # pragma: no cover - optional dependency
    from mcp.server.server import Server
except Exception:  # pragma: no cover
    Server = None  # type: ignore

from .tools.yt_transcript import fetch_transcript
from .tools.cefr_level import extract_vocab
from .tools.grammar import check_text
from .tools.tts import speak_to_file
from .tools.anki_tool import add_basic_note
from .orchestration.pipeline import LessonConfig, build_lesson


def create_server() -> "Server":  # type: ignore[return-type]
    """Create the MCP server and register all tools."""
    if Server is None:
        raise RuntimeError("anthropic-mcp SDK is not installed")

    server = Server("language-assistant")

    @server.tool("transcript.get")
    async def transcript_get(url: str) -> str:
        return fetch_transcript(url)

    @server.tool("vocab.extract")
    async def vocab_extract(text: str, limit: int = 20):
        return extract_vocab(text, limit=limit)

    @server.tool("grammar.check")
    async def grammar_check(text: str, language: str = "de"):
        return check_text(text, language=language)

    @server.tool("tts.speak")
    async def tts_speak(text: str, voice: str = "de-DE") -> str:
        return speak_to_file(text, f"tts_{abs(hash(text))}.mp3", voice=voice)

    @server.tool("anki.add_note")
    async def anki_add_note(front: str, back: str, deck: str, tags: List[str] | None = None):
        return add_basic_note(front, back, deck, tags=tags)

    @server.tool("lesson.build")
    async def lesson_build(url: str, deck: str, tag: str = "auto", limit: int = 15):
        cfg = LessonConfig(url=url, deck=deck, tag=tag, limit=limit)
        return build_lesson(cfg)

    return server


def list_tools() -> Dict[str, dict]:
    """Return a static description of the available tools."""
    return {
        "transcript.get": {"args": ["url: str"], "returns": "text"},
        "vocab.extract": {"args": ["text: str", "limit: int=20"], "returns": "list[dict]"},
        "grammar.check": {"args": ["text: str", "language: str='de'"], "returns": "list[dict]"},
        "tts.speak": {"args": ["text: str", "voice: str='de-DE'"], "returns": "path"},
        "anki.add_note": {
            "args": ["front: str", "back: str", "deck: str", "tags: list[str]=[]"],
            "returns": "note_id",
        },
        "lesson.build": {
            "args": ["url: str", "deck: str", "tag: str='auto'", "limit: int=15"],
            "returns": "dict",
        },
    }


async def run() -> None:
    """Entry point used by ``python -m app.mcp_server``."""
    server = create_server()
    await server.run()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    asyncio.run(run())
