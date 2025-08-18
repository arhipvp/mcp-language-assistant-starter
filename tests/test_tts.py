from pathlib import Path

from app.tools.tts import speak_to_file


def test_speak_to_file(tmp_path):
    out = tmp_path / "test.mp3"
    path = speak_to_file("Hallo Welt", str(out))
    p = Path(path)
    assert p.exists()
    assert p.stat().st_size > 0
