from app.mcp_tools import lesson


def test_make_card_no_image(monkeypatch):
    # Stub out external dependencies
    monkeypatch.setattr(lesson, "generate_sentence", lambda w: "Der Hund schläft.")
    monkeypatch.setattr(lesson, "translate_text", lambda text, src, tgt: "Собака спит")
    monkeypatch.setattr(lesson, "generate_image_file_genapi", lambda sentence: "")

    params = {}

    def fake_add_anki_note(front, back_html, deck, tags, media_path):
        params.update(
            front=front,
            back_html=back_html,
            deck=deck,
            tags=tags,
            media_path=media_path,
        )
        return 42

    monkeypatch.setattr(lesson, "add_anki_note", fake_add_anki_note)

    result = lesson.make_card("Hund", "de", "Deck", "tag")

    assert result == {
        "note_id": 42,
        "front": "Hund",
        "back": "<div>Перевод: Собака спит</div><div>Satz: Der Hund schläft.</div>",
        "image": "",
    }
    assert params["media_path"] is None
