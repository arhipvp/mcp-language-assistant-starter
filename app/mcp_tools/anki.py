import os
import base64
from typing import Any, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()
ANKI_URL = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")


def _invoke(action: str, **params) -> Any:
    """Invoke an action on the AnkiConnect API."""
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post(ANKI_URL, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data.get("result")


def store_media_file(path: str) -> str:
    """Upload a media file to Anki and return its filename."""
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return _invoke("storeMediaFile", filename=filename, data=encoded)


def add_anki_note(
    front: str,
    back_html: str,
    deck: str,
    tags: List[str],
    media_path: Optional[str],
) -> int:
    """Create a basic Anki note, optionally attaching media."""
    if media_path:
        media_filename = store_media_file(media_path)
        if "<img" not in back_html:
            back_html += f"<img src=\"{media_filename}\">"
    note = {
        "deckName": deck,
        "modelName": "Basic",
        "fields": {"Front": front, "Back": back_html},
        "tags": tags,
    }
    return _invoke("addNote", note=note)
