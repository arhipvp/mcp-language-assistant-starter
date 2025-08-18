import importlib
from types import SimpleNamespace
import pytest

from app.net.http import NetworkError


# helper to import module after setting env
def _import_module(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "m")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "img")
    monkeypatch.setenv("ANKI_DECK", "deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    # не обязательно для этого модуля, но пусть будет для консистентности окружения
    monkeypatch.setenv("GENAPI_API_KEY", "x")

    import app.settings as settings_module
    importlib.reload(settings_module)

    module = importlib.import_module("app.mcp_tools.openrouter_chat")
    return importlib.reload(module)


def test_chat_success(monkeypatch):
    oc = _import_module(monkeypatch)

    def fake_request(method, url, headers=None, json=None, timeout=None):
        assert method == "POST"
        assert json["model"] == "m"
        assert json["messages"] == [{"role": "user", "content": "hi"}]
        return {"choices": [{"message": {"content": "hello"}}]}

    monkeypatch.setattr(oc, "request_json", fake_request)

    out = oc.chat([{"role": "user", "content": "hi"}])
    assert out == "hello"


def test_chat_missing_config(monkeypatch):
    oc = _import_module(monkeypatch)

    # no API key
    monkeypatch.setattr(
        oc,
        "settings",
        SimpleNamespace(OPENROUTER_API_KEY="", OPENROUTER_TEXT_MODEL="m"),
    )

    def fail_request(*a, **k):  # should not be called
        raise AssertionError("request_json should not be called")

    monkeypatch.setattr(oc, "request_json", fail_request)

    with pytest.raises(NetworkError) as exc:
        oc.chat([{"role": "user", "content": "hi"}])

    assert exc.value.code == "config"
