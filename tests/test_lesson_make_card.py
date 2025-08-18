import sys
import types


def test_make_card_happy_path(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "x")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "x")
    monkeypatch.setenv("ANKI_DECK", "Deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("GENAPI_API_KEY", "x")

    fake_text = types.ModuleType("app.mcp_tools.text")
    fake_text.generate_sentence = lambda w: "Der Hund schläft."
    fake_text.translate_text = lambda text, src, tgt: "Собака спит"
    monkeypatch.setitem(sys.modules, "app.mcp_tools.text", fake_text)

    fake_image = types.ModuleType("app.mcp_tools.image")
    fake_image.generate_image_file = lambda sentence: ""
    monkeypatch.setitem(sys.modules, "app.mcp_tools.image", fake_image)

    fake_anki = types.ModuleType("app.mcp_tools.anki")
    fake_anki.add_anki_note = lambda **kwargs: 123
    monkeypatch.setitem(sys.modules, "app.mcp_tools.anki", fake_anki)
    monkeypatch.delitem(sys.modules, "app.mcp_tools.lesson", raising=False)
    from app.mcp_tools.lesson import make_card

    result = make_card("Hund", "de", "Deck", "tag")

    assert set(result) == {"note_id", "front", "back", "image"}
    assert result["note_id"] == 123
    assert result["front"] == "Hund"
    assert result["back"] == "<div>Перевод: Собака спит</div><div>Satz: Der Hund schläft.</div>"
    assert result["image"] == ""
