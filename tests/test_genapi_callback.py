import importlib
import importlib
from types import SimpleNamespace


def _import_client(monkeypatch):
    # minimal env vars so that app.settings can import once
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "m")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "img")
    monkeypatch.setenv("ANKI_DECK", "deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    module = importlib.import_module("app.genapi")
    return importlib.reload(module)


def test_callback_included(monkeypatch):
    genapi = _import_client(monkeypatch)

    calls = {}

    def fake_request(method, url, json=None, headers=None, timeout=None):
        calls["json"] = json
        return {"request_id": "123"}

    monkeypatch.setattr(genapi, "request_json", fake_request)
    monkeypatch.setattr(
        genapi,
        "settings",
        SimpleNamespace(GENAPI_CALLBACK_URL="https://cb", GENAPI_IS_SYNC=False),
    )
    out = genapi.create_task({"prompt": "hi"})
    assert out == {"request_id": "123"}
    assert calls["json"]["callback_url"] == "https://cb"


def test_callback_omitted(monkeypatch):
    genapi = _import_client(monkeypatch)

    calls = []

    def fake_request(method, url, json=None, headers=None, timeout=None):
        calls.append(json)
        return {}

    monkeypatch.setattr(genapi, "request_json", fake_request)
    monkeypatch.setattr(
        genapi, "settings", SimpleNamespace(GENAPI_CALLBACK_URL=None, GENAPI_IS_SYNC=False)
    )
    genapi.create_task({"prompt": "hi"})
    assert "callback_url" not in calls[-1]

    monkeypatch.setattr(
        genapi, "settings", SimpleNamespace(GENAPI_CALLBACK_URL="https://cb", GENAPI_IS_SYNC=True)
    )
    genapi.create_task({"prompt": "hi"})
    assert "callback_url" not in calls[-1]
