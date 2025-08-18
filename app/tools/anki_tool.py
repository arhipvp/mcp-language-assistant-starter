
import os, json, requests
from typing import List
from dotenv import load_dotenv

load_dotenv()
ANKI_URL = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")

def _invoke(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    r = requests.post(ANKI_URL, json=payload, timeout=15)
    r.raise_for_status()
    out = r.json()
    if out.get("error"):
        raise RuntimeError(out["error"])
    return out["result"]

def add_basic_note(front: str, back: str, deck: str, tags: List[str] = None) -> int:
    tags = tags or []
    note = {
        "deckName": deck,
        "modelName": "Basic",
        "fields": {"Front": front, "Back": back},
        "tags": tags,
    }
    return _invoke("addNote", note=note)
