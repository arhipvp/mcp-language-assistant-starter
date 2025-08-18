from app.mcp_tools import text


class DummyLLM:
    def chat(self, messages):
        system = messages[0]["content"]
        if system.startswith("Translate to"):
            return {"choices": [{"message": {"content": '"собака"'}}]}
        return {"choices": [{"message": {"content": "Der Hund spielt."}}]}


def test_generate_sentence(monkeypatch):
    monkeypatch.setattr(text, "llm_text", DummyLLM())
    out = text.generate_sentence("Hund")
    assert out == "Der Hund spielt."


def test_translate_text(monkeypatch):
    monkeypatch.setattr(text, "llm_text", DummyLLM())
    out = text.translate_text("Hund", "de", "ru")
    assert out == "собака"
