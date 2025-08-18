import base64
import os
import time
from typing import List
import requests
from dotenv import load_dotenv

load_dotenv()

ANKI_CONNECT_URL = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")


def _invoke(action: str, **params):
    payload = {"action": action, "version": 6, "params": params}
    for attempt in range(3):
        try:
            resp = requests.post(ANKI_CONNECT_URL, json=payload, timeout=30)
            resp.raise_for_status()
            out = resp.json()
            if out.get("error"):
                raise RuntimeError(out["error"])
            return out["result"]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Anki invocation failed")


def add_anki_note(front: str, back: str, deck: str, tags: List[str], media_path: str) -> int:
    """Добавить карточку в Anki с опциональным изображением."""
    tags = tags or []
    back_html = back
    if media_path:
        with open(media_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        filename = os.path.basename(media_path)
        _invoke("storeMediaFile", filename=filename, data=data)
        back_html += f'<br><img src="{filename}">'
    note = {
        "deckName": deck,
        "modelName": "Basic",
        "fields": {"Front": front, "Back": back_html},
        "tags": tags,
    }
    return _invoke("addNote", note=note)
