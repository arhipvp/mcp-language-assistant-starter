
def test_make_cards_from_list_handles_errors(monkeypatch):
    # satisfy settings import
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "x")
    monkeypatch.setenv("ANKI_DECK", "Deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")

    from app.mcp_tools import batch

    calls = []

    def fake_make_card(word, lang, deck, tag):
        calls.append(word)
        if word == "bad":
            raise RuntimeError("boom")
        return {"word": word}

    monkeypatch.setattr(batch, "make_card", fake_make_card)

    words = ["good", "bad", "great"]
    result = batch.make_cards_from_list(words, "de", "Deck", "tag")

    # ensure make_card was called for all words
    assert calls == words
    # ensure error for failing word captured
    assert result[1] == {"word": "bad", "error": "boom"}
    # ensure successful words return their data
    assert result[0] == {"word": "good"}
    assert result[2] == {"word": "great"}
