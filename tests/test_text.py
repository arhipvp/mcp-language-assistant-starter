from types import SimpleNamespace

from app.mcp_tools import text


def test_generate_sentence_fallback(monkeypatch):
    monkeypatch.setattr(text, "llm_text", None)
    monkeypatch.setattr(
        text,
        "settings",
        SimpleNamespace(OPENROUTER_API_KEY="k", OPENROUTER_TEXT_MODEL="m"),
    )

    def fake_request_json(method, url, *, headers=None, json=None, timeout=30):  # noqa: D401
        return {"choices": [{"message": {"content": "Der Hund rennt schnell zum Park."}}]}

    monkeypatch.setattr(text, "request_json", fake_request_json)

    sentence = text.generate_sentence("Hund")
    words = sentence.split()
    assert 6 <= len(words) <= 12
    assert any("hund" in w.lower() for w in words)


def test_translate_text_fallback(monkeypatch):
    monkeypatch.setattr(text, "llm_text", None)
    monkeypatch.setattr(
        text,
        "settings",
        SimpleNamespace(OPENROUTER_API_KEY="k", OPENROUTER_TEXT_MODEL="m"),
    )

    def fake_request_json(method, url, *, headers=None, json=None, timeout=30):  # noqa: D401
        return {"choices": [{"message": {"content": '"собака"'}}]}

    monkeypatch.setattr(text, "request_json", fake_request_json)

    translated = text.translate_text("Hund", "de", "ru")
    assert translated == "собака"
