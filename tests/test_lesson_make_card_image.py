import base64
from pathlib import Path
from types import SimpleNamespace
import importlib


def _prepare(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "text-model")
    monkeypatch.setenv("ANKI_DECK", "Deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("GENAPI_API_KEY", "key")

    lesson = importlib.reload(importlib.import_module("app.mcp_tools.lesson"))
    image = importlib.reload(importlib.import_module("app.mcp_tools.image"))
    import sys
    monkeypatch.setitem(sys.modules, "app.mcp_tools.lesson", lesson)
    monkeypatch.setitem(sys.modules, "app.mcp_tools.image", image)

    monkeypatch.setattr(lesson, "generate_sentence", lambda w: "Der Hund schläft.")
    monkeypatch.setattr(lesson, "translate_text", lambda text, src, tgt: "Собака спит")

    called = {}

    def fake_add_anki_note(front, back_html, deck, tags=None, media_path=None):
        called.update(front=front, back_html=back_html, deck=deck, tags=tags or [], media_path=media_path)
        return 42

    monkeypatch.setattr(lesson, "add_anki_note", fake_add_anki_note)

    fake_settings = SimpleNamespace(
        GENAPI_API_KEY="key",
        GENAPI_MODEL_ID="m",
        GENAPI_SIZE="1024x1024",
        GENAPI_QUALITY="low",
        GENAPI_OUTPUT_FORMAT="png",
        GENAPI_IS_SYNC=True,
        GENAPI_CALLBACK_URL=None,
    )
    monkeypatch.setattr(image, "settings", fake_settings)
    monkeypatch.setattr(image, "MEDIA_DIR", tmp_path)

    return lesson, image, called


def test_make_card_image_success(monkeypatch, tmp_path):
    lesson, image, called = _prepare(monkeypatch, tmp_path)

    img_bytes = b"img-bytes"
    b64 = base64.b64encode(img_bytes).decode()
    resp = type("R", (), {"status_code": 200, "text": "", "json": lambda self: {"data": [{"b64_json": b64}]}})()
    monkeypatch.setattr(image.requests, "post", lambda *a, **k: resp)

    result = lesson.make_card("Hund", "de", "Deck", "tag")

    assert result["note_id"] == 42
    assert result["front"] == "Hund"
    assert result["image"]
    assert result["image"] in result["back"]
    assert result["message"] == "Карточка создана с изображением"

    assert (tmp_path / Path(result["image"]).name).read_bytes() == img_bytes
    assert called["back_html"] == result["back"]
    assert called["media_path"] == result["image"]


def test_make_card_image_failure(monkeypatch, tmp_path):
    lesson, image, called = _prepare(monkeypatch, tmp_path)

    resp = type(
        "R",
        (),
        {"status_code": 500, "text": "boom", "json": lambda self: (_ for _ in ()).throw(RuntimeError("boom"))},
    )()
    monkeypatch.setattr(image.requests, "post", lambda *a, **k: resp)

    result = lesson.make_card("Hund", "de", "Deck", "tag")

    assert result["note_id"] == 42
    assert result["front"] == "Hund"
    assert result["image"] == ""
    assert "<img" not in result["back"]
    assert result["message"] == "Карточка создана без изображения"

    assert called["media_path"] is None
    assert "<img" not in called["back_html"]
    assert list(tmp_path.iterdir()) == []

