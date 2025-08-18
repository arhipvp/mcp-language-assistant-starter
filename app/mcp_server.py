"""Minimal MCP server wiring the language tools together.

The implementation is intentionally lightweight and only depends on the
`mcp` package if it is available. When the SDK is missing the
module still exposes a :func:`list_tools` helper so that downstream code
can introspect the offered capabilities.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict

from . import setup_logging, log_effective_settings

try:  # pragma: no cover - optional dependency
    import mcp
except Exception:  # pragma: no cover
    mcp = None  # type: ignore

from .tools.yt_transcript import fetch_transcript
from .tools.cefr_level import extract_vocab
from .tools.grammar import check_text
from .tools.tts import speak_to_file
from .tools.anki_tool import add_basic_note
from .tools.health import check_health
from .orchestration.pipeline import LessonConfig, build_lesson
from .mcp_tools.lesson import make_card as make_lesson_card
from .mcp_tools.health_genapi import genapi_check

from .settings import settings  # noqa: F401  - trigger config loading

from .tool_logging import log_tool



def lesson_make_card(word: str, lang: str, deck: str, tag: str) -> dict:
    """Create a flashcard for a word.

    Thin wrapper that delegates to :func:`app.mcp_tools.lesson.make_card`.
    """
    return make_lesson_card(word, lang, deck, tag)


def create_server() -> "mcp.server.FastMCP":  # type: ignore[return-type]
    """Create the MCP server and register all tools."""
    if mcp is None:
        raise RuntimeError("MCP SDK ('mcp') is not installed. Run: pip install mcp")

    logger = logging.getLogger(__name__)
    logger.info("MCP version: %s", getattr(mcp, "__version__", "unknown"))

    server = mcp.server.FastMCP("language-assistant")

    @log_tool(server, "transcript.get")
    async def transcript_get(url: str) -> str:
        return fetch_transcript(url)

    @log_tool(server, "vocab.extract")
    async def vocab_extract(text: str, limit: int = 20):
        return extract_vocab(text, limit=limit)

    @log_tool(server, "grammar.check")
    async def grammar_check(text: str, language: str = "de"):
        return check_text(text, language=language)

    @log_tool(server, "tts.speak")
    async def tts_speak(text: str, voice: str = "de-DE") -> str:
        return speak_to_file(text, f"tts_{abs(hash(text))}.mp3", voice=voice)

    @log_tool(server, "anki.add_note")
    async def anki_add_note(front: str, back: str, deck: str, tags: list[str] | None = None):
        return add_basic_note(front, back, deck, tags=tags)

    @log_tool(server, "lesson.build")
    async def lesson_build(url: str, deck: str, tag: str = "auto", limit: int = 15):
        cfg = LessonConfig(url=url, deck=deck, tag=tag, limit=limit)
        return build_lesson(cfg)

    @log_tool(server, "lesson.make_card")
    async def lesson_make_card_tool(word: str, lang: str, deck: str, tag: str) -> dict:
        return make_lesson_card(word, lang, deck, tag)

    @server.tool("server.health")
    async def server_health() -> dict:
        return check_health()

    @log_tool(server, "health.genapi_check")
    async def health_genapi_check_tool() -> dict:
        return genapi_check()

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
        "lesson.make_card": {
            "args": ["word: str", "lang: str", "deck: str", "tag: str"],
            "returns": "dict",
        },
        "server.health": {"args": [], "returns": "dict"},
        "health.genapi_check": {"args": [], "returns": "dict"},
    }


async def run() -> None:
    """Entry point used by ``python -m app.mcp_server``."""
    setup_logging()
    logger = logging.getLogger(__name__)
    log_effective_settings(logger)
    logger.info("Application starting...")
    server = create_server()
    logger.info("MCP server listening on stdio.")
    await server.run_stdio_async()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    asyncio.run(run())
