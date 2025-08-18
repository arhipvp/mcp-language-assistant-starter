from __future__ import annotations

import base64
import os
from typing import Any, List, Optional

from app.net.http import NetworkError, request_json
from app.settings import settings


def _invoke(action: str, **params) -> Any:
    """Вызов метода AnkiConnect через общий HTTP-слой."""
    payload = {"action": action, "version": 6, "params": params}
    out = request_json("POST", settings.ANKI_CONNECT_URL, json=payload, timeout=30)
    if out.get("error"):
        # единый формат сетевых ошибок
        raise NetworkError("anki-error", out["error"], {"action": action})
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
