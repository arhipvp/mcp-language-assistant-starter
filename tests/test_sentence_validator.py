import pytest

from app.mcp_tools import text
from app.net.http import NetworkError


def test_includes_target_normalization():
    assert text._includes_target("Straße", "Die Strasse ist breit.")
    assert not text._includes_target("Straße", "Das Haus ist groß.")
    assert text._includes_target("Hund", "Der Hund! spielt.")
    assert not text._includes_target("Hund", "Hundert Leute kommen.")


def test_generate_sentence_retries(monkeypatch):
    responses = [
        "Die Katze schläft.",
        "Ein Vogel fliegt.",
        "Der Hund spielt im Garten.",
    ]
    calls = []

    def fake_chat(messages):
        calls.append(1)
        return responses[len(calls) - 1]

    monkeypatch.setattr(text, "_chat", fake_chat)
    sentence = text.generate_sentence("Hund")
    assert sentence == "Der Hund spielt im Garten."
    assert len(calls) == 3


def test_generate_sentence_raises_after_three_attempts(monkeypatch):
    responses = [
        "Die Katze schläft.",
        "Ein Vogel fliegt.",
        "Der Vogel sitzt.",
    ]
    calls = []

    def fake_chat(messages):
        calls.append(1)
        return responses[len(calls) - 1]

    monkeypatch.setattr(text, "_chat", fake_chat)
    with pytest.raises(NetworkError) as exc:
        text.generate_sentence("Hund")
    assert exc.value.code == "validation"
    assert len(calls) == 3
