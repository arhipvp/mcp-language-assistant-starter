import base64
import os
from typing import Any, List, Optional

from dotenv import load_dotenv

from app.net.http import NetworkError, request_json

load_dotenv()

ANKI_CONNECT_URL = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765")


def _invoke(action: str, **params) -> Any:
    """Вызов метода AnkiConnect с экспоненциальным бэкоффом."""
    payload = {"action": action, "version": 6, "params": params}
    out = request_json("POST", ANKI_CONNECT_URL, json=payload, timeout=30)
    if out.get("error"):
        raise NetworkError("anki-error", out["error"])
    return out.get("result")


def store_media_file(path: str) -> str:
    """Загрузить файл в медиа Anki и вернуть итоговое имя файла."""
    filename = os.path.basename(path)
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return _invoke("storeMediaFile", filename=filename, data=encoded)


def add_anki_note(
    front: str,
    back_html: str,
    deck: str,
    tags: Optional[List[str]] = None,
    media_path: Optional[str] = None,
) -> int:
    """Создать базовую карточку Anki с опциональным изображением на обороте."""
    tags = tags or []

    if media_path:
        media_filename = store_media_file(media_path)
        # Добавляем картинку, если пользователь ещё не вставил <img> вручную
        if "<img" not in back_html:
            back_html += f'<br><img src="{media_filename}">'

    note = {
        "deckName": deck,
        "modelName": "Basic",
        "fields": {"Front": front, "Back": back_html},
        "tags": tags,
    }
    # Возвращает ID заметки (int)
    return _invoke("addNote", note=note)
