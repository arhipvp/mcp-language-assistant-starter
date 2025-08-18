import importlib.util

import requests

from app.tools import health


class DummyResp:
    def __init__(self, data=None, status=200):
        self._data = data or {}
        self.status_code = status

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def test_check_health(monkeypatch):
    calls = {"get": 0, "post": 0}

    def fake_get(url, headers=None, timeout=None):
        calls["get"] += 1
        return DummyResp()

    def fake_post(url, json=None, timeout=None):
        calls["post"] += 1
        return DummyResp({"result": "2.1.0", "error": None})

    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "m-text")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "m-img")
    monkeypatch.setenv("ANKI_CONNECT_URL", "http://anki")
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())

    # сброс кеша
    health._last_result = None
    health._last_checked = 0.0

    res1 = health.check_health()
    assert res1["openrouter_text"]["status"] == "ok"
    assert res1["openrouter_text"]["message"] == "m-text"
    assert res1["openrouter_image"]["status"] == "ok"
    assert res1["openrouter_image"]["message"] == "m-img"
    assert res1["anki"]["status"] == "ok"
    assert res1["anki"]["message"] == "2.1.0"
    assert res1["tts"]["status"] == "ok"

    assert calls["get"] == 2
    assert calls["post"] == 1

    # повторный вызов использует кеш
    res2 = health.check_health()
    assert calls["get"] == 2
    assert calls["post"] == 1
    assert res2 == res1
