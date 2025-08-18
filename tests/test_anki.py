import base64
import os

import pytest

for key in [
    "OPENROUTER_API_KEY",
    "OPENROUTER_TEXT_MODEL",
    "OPENROUTER_IMAGE_MODEL",
    "ANKI_DECK",
    "TELEGRAM_BOT_TOKEN",
    "GENAPI_API_KEY",
]:
    os.environ.setdefault(key, "test")

from app.mcp_tools import anki
from app.settings import settings
from app.net.http import NetworkError


def test_invoke_calls_request_json(monkeypatch):
    calls = {}

    def fake_request_json(method, url, json=None, timeout=None, headers=None):
        calls['method'] = method
        calls['url'] = url
        calls['json'] = json
        calls['timeout'] = timeout
        return {"error": None, "result": 42}

    monkeypatch.setattr(anki, "request_json", fake_request_json)

    result = anki._invoke("testAction", foo="bar")

    assert result == 42
    assert calls['method'] == "POST"
    assert calls['url'] == settings.ANKI_CONNECT_URL
    assert calls['timeout'] == 30
    assert calls['json'] == {"action": "testAction", "version": 6, "params": {"foo": "bar"}}


def test_invoke_error(monkeypatch):
    def fake_request_json(method, url, json=None, timeout=None, headers=None):
        return {"error": "boom", "result": None}

    monkeypatch.setattr(anki, "request_json", fake_request_json)

    with pytest.raises(NetworkError) as exc:
        anki._invoke("do", bar=1)

    assert exc.value.code == "anki-error"
    assert exc.value.message == "boom"
    assert exc.value.details == {"action": "do"}


def test_store_media_file(monkeypatch, tmp_path):
    payload = {}

    def fake_request_json(method, url, json=None, timeout=None, headers=None):
        payload.update(json)
        return {"error": None, "result": "pic.png"}

    monkeypatch.setattr(anki, "request_json", fake_request_json)

    media = tmp_path / "pic.png"
    media.write_bytes(b"data")

    result = anki.store_media_file(str(media))

    assert result == "pic.png"
    assert payload["action"] == "storeMediaFile"
    params = payload["params"]
    assert params["filename"] == "pic.png"
    expected = base64.b64encode(b"data").decode("ascii")
    assert params["data"] == expected


def test_add_anki_note(monkeypatch, tmp_path):
    calls = []

    def fake_request_json(method, url, json=None, timeout=None, headers=None):
        calls.append(json)
        if json["action"] == "storeMediaFile":
            return {"error": None, "result": json["params"]["filename"]}
        if json["action"] == "addNote":
            return {"error": None, "result": 99}
        raise AssertionError("unexpected action")

    monkeypatch.setattr(anki, "request_json", fake_request_json)

    media = tmp_path / "img.png"
    media.write_bytes(b"img")

    note_id = anki.add_anki_note(
        front="Hund",
        back_html="<div>Back</div>",
        deck="Deck",
        tags=["tag"],
        media_path=str(media),
    )

    assert note_id == 99
    # first call is storeMediaFile
    assert calls[0]["action"] == "storeMediaFile"
    # second call is addNote
    assert calls[1]["action"] == "addNote"
    note = calls[1]["params"]["note"]
    assert note["deckName"] == "Deck"
    assert note["fields"]["Front"] == "Hund"
    assert '<img src="img.png">' in note["fields"]["Back"]
    assert note["tags"] == ["tag"]
