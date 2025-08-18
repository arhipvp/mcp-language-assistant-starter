from app.mcp_tools import anki


def test_add_anki_note_with_media(monkeypatch, tmp_path):
    calls = []

    def fake_invoke(action, **params):
        calls.append((action, params))
        if action == "storeMediaFile":
            return params["filename"]
        if action == "addNote":
            return 77
        raise ValueError(action)

    monkeypatch.setattr(anki, "_invoke", fake_invoke)

    media = tmp_path / "pic.png"
    media.write_bytes(b"data")

    note_id = anki.add_anki_note(
        front="Hund",
        back_html="<div>Back</div>",
        deck="Deck",
        tags=["tag"],
        media_path=str(media),
    )

    assert note_id == 77
    assert calls[0][0] == "storeMediaFile"
    assert calls[0][1]["filename"] == "pic.png"
    assert calls[1][0] == "addNote"
    note = calls[1][1]["note"]
    assert note["fields"]["Front"] == "Hund"
    assert '<img src="pic.png">' in note["fields"]["Back"]
    assert note["tags"] == ["tag"]
