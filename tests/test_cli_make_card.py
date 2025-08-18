import json
import runpy


def test_make_card_cli(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("OPENROUTER_TEXT_MODEL", "x")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "x")
    monkeypatch.setenv("ANKI_DECK", "Deck")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")

    from app.mcp_tools import lesson

    called = {}

    def fake_make_card(word, lang, deck, tag):
        called['args'] = (word, lang, deck, tag)
        return {'front': 'Hund', 'back': 'Back', 'image': 'img.png', 'note_id': 42}

    monkeypatch.setattr(lesson, 'make_card', fake_make_card)

    module_globals = runpy.run_path('cli/make_card.py', run_name='__not_main__')
    exit_code = module_globals['main']([
        '--word', 'Hund',
        '--lang', 'de',
        '--deck', 'Deck',
        '--tag', 'tag'
    ])

    assert exit_code == 0
    assert called['args'] == ('Hund', 'de', 'Deck', 'tag')
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == {'front': 'Hund', 'back': 'Back', 'image': 'img.png', 'note_id': 42}
