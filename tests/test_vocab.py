from app.tools.cefr_level import extract_vocab


def test_extract_vocab_has_level():
    text = "Hallo Welt, wir sprechen freundlich und lernen Deutsch."
    items = extract_vocab(text, limit=10)
    vocab = {i["term"]: i for i in items}
    assert "freundlich" in vocab
    assert vocab["freundlich"]["level"] == "B1"
