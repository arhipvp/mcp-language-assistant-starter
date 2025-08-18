import base64
import os
import base64
import os
import time
from typing import Any, List, Optional

import requests

from app.settings import settings


def _invoke(action: str, **params) -> Any:
    """Вызов метода AnkiConnect с 3 попытками и экспоненциальной паузой."""
    payload = {"action": action, "version": 6, "params": params}
    for attempt in range(3):
        try:
            resp = requests.post(settings.ANKI_CONNECT_URL, json=payload, timeout=30)
            resp.raise_for_status()
            out = resp.json()
            if out.get("error"):
                raise RuntimeError(out["error"])
            return out.get("result")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Anki invocation failed")


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
