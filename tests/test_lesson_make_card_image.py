from types import SimpleNamespace
from pathlib import Path
import importlib
import os


def _prepare(monkeypatch, tmp_path):
    # Ensure required env vars for settings
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "text-model")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "model")
    monkeypatch.setenv("ANKI_DECK", "Deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")

    lesson = importlib.reload(importlib.import_module("app.mcp_tools.lesson"))
    image = importlib.reload(importlib.import_module("app.mcp_tools.image"))
    # ensure modules cleaned after test
    import sys
    monkeypatch.setitem(sys.modules, "app.mcp_tools.lesson", lesson)
    monkeypatch.setitem(sys.modules, "app.mcp_tools.image", image)

    # stub text functions
    monkeypatch.setattr(lesson, "generate_sentence", lambda w: "Der Hund schläft.")
    monkeypatch.setattr(lesson, "translate_text", lambda text, src, tgt: "Собака спит")

    # stub anki function to capture back_html and media_path
    called = {}

    def fake_add_anki_note(front, back_html, deck, tags=None, media_path=None):
        tags = tags or []
        if media_path and "<img" not in back_html:
            back_html += f'<br><img src="{Path(media_path).name}">'
        called.update(front=front, back_html=back_html, deck=deck, tags=tags, media_path=media_path)
        return 42

    monkeypatch.setattr(lesson, "add_anki_note", fake_add_anki_note)

    # configure image module
    monkeypatch.setattr(image, "settings", SimpleNamespace(OPENROUTER_API_KEY="key", OPENROUTER_IMAGE_MODEL="model"))
    monkeypatch.setattr(image, "MEDIA_DIR", tmp_path)

    return lesson, image, called


def test_make_card_image_success(monkeypatch, tmp_path):
    lesson, image, called = _prepare(monkeypatch, tmp_path)

    img_bytes = b"img-bytes"

    def fake_request_json(method, url, headers=None, json=None, timeout=None):
        return {"data": [{"url": "http://example.com/img.png"}]}

    class DummyResp:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=None):
        return DummyResp(img_bytes)

    monkeypatch.setattr(image, "request_json", fake_request_json)
    monkeypatch.setattr(image.requests, "get", fake_get)

    result = lesson.make_card("Hund", "de", "Deck", "tag")

    assert result["note_id"] == 42
    assert result["front"] == "Hund"
    assert result["back"] == "<div>Перевод: Собака спит</div><div>Satz: Der Hund schläft.</div>"
    assert result["image"]

    # file exists
    assert (tmp_path / result["image"]).read_bytes() == img_bytes
    # anki note received img tag
    assert "<img" in called["back_html"]
    assert os.fspath(called["media_path"]) == str(tmp_path / result["image"])


def test_make_card_image_failure(monkeypatch, tmp_path):
    lesson, image, called = _prepare(monkeypatch, tmp_path)

    def fake_request_json(method, url, headers=None, json=None, timeout=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(image, "request_json", fake_request_json)

    result = lesson.make_card("Hund", "de", "Deck", "tag")

    assert result["note_id"] == 42
    assert result["front"] == "Hund"
    assert result["back"] == "<div>Перевод: Собака спит</div><div>Satz: Der Hund schläft.</div>"
    assert result["image"] == ""

    assert called["media_path"] is None
    assert "<img" not in called["back_html"]
    assert list(tmp_path.iterdir()) == []
