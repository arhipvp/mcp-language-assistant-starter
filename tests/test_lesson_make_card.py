import sys
import types
import importlib


def test_make_card_happy_path(monkeypatch):
    # ENV для прохождения внутренних проверок
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "x")
    monkeypatch.setenv("ANKI_DECK", "Deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("GENAPI_API_KEY", "x")
    # провайдер оставляем по умолчанию (openrouter)

    # Фейки для text
    fake_text = types.ModuleType("app.mcp_tools.text")
    fake_text.generate_sentence = lambda w: "Der Hund schläft."
    fake_text.translate_text = lambda text, src, tgt: "Собака спит"
    monkeypatch.setitem(sys.modules, "app.mcp_tools.text", fake_text)

    # Фейки для image
    fake_image = types.ModuleType("app.mcp_tools.image")
    fake_image.generate_image_file = lambda sentence: ""
    monkeypatch.setitem(sys.modules, "app.mcp_tools.image", fake_image)

    # Фейки для anki
    fake_anki = types.ModuleType("app.mcp_tools.anki")
    fake_anki.add_anki_note = lambda **kwargs: 123
    monkeypatch.setitem(sys.modules, "app.mcp_tools.anki", fake_anki)

    # Перезагружаем lesson, чтобы он импортировал фейковые модули
    lesson = importlib.reload(importlib.import_module("app.mcp_tools.lesson"))

    result = lesson.make_card("Hund", "de", "Deck", "tag")

    assert set(result) == {"note_id", "front", "back", "image", "message"}
    assert result["note_id"] == 123
    assert result["front"] == "Hund"
    assert (
        result["back"]
        == "<div>Перевод: Собака спит</div><div>Satz: Der Hund schläft.</div>"
    )
    assert result["image"] == ""
    assert result["message"] == "Карточка создана без изображения"
