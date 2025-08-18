
"""Placeholder for a real MCP server.

TODO: Replace with Anthropic MCP server implementation,
register tools from `app.tools.*` and expose composite flows.

For now, this file only documents expected tool signatures.
"""

from typing import List, Dict

def list_tools() -> Dict[str, dict]:
    return {
        "transcript.get": {"args": ["url: str"], "returns": "text"},
        "vocab.extract": {"args": ["text: str", "limit: int=20"], "returns": "list[dict]"},
        "grammar.check": {"args": ["text: str", "language: str='de'"], "returns": "list[dict]"},
        "tts.speak": {"args": ["text: str", "voice: str='de-DE'"], "returns": "bytes|path"},
        "anki.add_note": {"args": ["front: str", "back: str", "deck: str", "tags: list[str]=[]"], "returns": "note_id"},
    }
