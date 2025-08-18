import io
import os
from typing import List

for key in [
    "OPENROUTER_API_KEY",
    "OPENROUTER_TEXT_MODEL",
    "OPENROUTER_IMAGE_MODEL",
    "ANKI_DECK",
    "TELEGRAM_BOT_TOKEN",
]:
    os.environ.setdefault(key, "test")

import app.mcp_tools.anki as anki


class DummyFile(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def fake_open(*args, **kwargs):
    return DummyFile(b"data")


def fake_request_json_factory(calls: List[dict]):
    def fake_request_json(method, url, json=None, timeout=None, headers=None):
        calls.append(json)
        action = json["action"]
        if action == "storeMediaFile":
            return {"error": None, "result": json["params"]["filename"]}
        if action == "addNote":
            return {"error": None, "result": 1}
        raise AssertionError(f"unexpected action {action}")

    return fake_request_json


def test_payload_contains_model_and_fields_and_appends_img(monkeypatch):
    calls = []
    monkeypatch.setattr(anki, "request_json", fake_request_json_factory(calls))
    monkeypatch.setattr("builtins.open", fake_open)

    note_id = anki.add_anki_note(
        front="Q",
        back_html="A",
        deck="Deck",
        tags=["tag"],
        media_path="pic.png",
    )

    assert note_id == 1
    add_note = [c for c in calls if c["action"] == "addNote"][0]
    note = add_note["params"]["note"]
    assert note["modelName"] == "Basic"
    assert note["fields"] == {"Front": "Q", "Back": 'A<br><img src="pic.png">'}


def test_payload_does_not_duplicate_img(monkeypatch):
    calls = []
    monkeypatch.setattr(anki, "request_json", fake_request_json_factory(calls))
    monkeypatch.setattr("builtins.open", fake_open)

    back_with_img = 'A<br><img src="existing.png">'
    anki.add_anki_note(
        front="Q",
        back_html=back_with_img,
        deck="Deck",
        tags=["tag"],
        media_path="pic.png",
    )

    add_note = [c for c in calls if c["action"] == "addNote"][0]
    note = add_note["params"]["note"]
    assert note["fields"]["Back"] == back_with_img
