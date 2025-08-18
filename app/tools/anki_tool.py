import os
import requests
from typing import List, Optional

from app.settings import settings

ANKI_URL = settings.ANKI_CONNECT_URL


def _invoke(action: str, **params):
    payload = {"action": action, "version": 6, "params": params}
    r = requests.post(ANKI_URL, json=payload, timeout=15)
    r.raise_for_status()
    out = r.json()
    if out.get("error"):
        raise RuntimeError(out["error"])
    return out["result"]


def add_basic_note(
    front: str,
    back: str,
    deck: str,
    tags: Optional[List[str]] = None,
    audio_path: Optional[str] = None,
) -> int:
    """Add a basic Anki note with optional audio attachment."""
    tags = tags or []
    note = {
        "deckName": deck,
        "modelName": "Basic",
        "fields": {"Front": front, "Back": back},
        "tags": tags,
    }
    if audio_path:
        note["audio"] = [
            {
                "path": audio_path,
                "filename": os.path.basename(audio_path),
                "fields": ["Back"],
            }
        ]
    return _invoke("addNote", note=note)
