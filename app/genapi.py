"""Lightweight GenAPI client with optional callback support."""
from __future__ import annotations

from typing import Any, Dict

from app.net.http import request_json
from app.settings import settings

API_URL = "https://gen-api.ru/task"


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a task in GenAPI.

    If ``settings.GENAPI_CALLBACK_URL`` is set and ``settings.GENAPI_IS_SYNC`` is
    ``False``, the ``callback_url`` field is added to the payload so that the
    server sends the result asynchronously instead of requiring polling.
    """
    data = dict(payload)
    if settings.GENAPI_CALLBACK_URL and not settings.GENAPI_IS_SYNC:
        data["callback_url"] = settings.GENAPI_CALLBACK_URL
    return request_json("POST", API_URL, json=data, timeout=30)
