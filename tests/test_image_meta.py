import base64
import hashlib
from pathlib import Path
from types import SimpleNamespace

from app.mcp_tools import image


def _prepare(monkeypatch, tmp_path):
    fake_settings = SimpleNamespace(
        OPENROUTER_API_KEY="key", OPENROUTER_IMAGE_MODEL="model"
    )
    monkeypatch.setattr(image, "settings", fake_settings)
    monkeypatch.setattr(image, "MEDIA_DIR", tmp_path)


def test_deterministic_name_and_caching(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    img_bytes = b"fake-bytes"
    b64 = base64.b64encode(img_bytes).decode()
    calls = []

    def fake_request_json(method, url, headers=None, json=None, timeout=None):
        calls.append(1)
        return {"data": [{"b64_json": b64}]}

    monkeypatch.setattr(image, "request_json", fake_request_json)

    meta1 = image.generate_image_file("Hallo")
    meta2 = image.generate_image_file("Hallo")

    expected_hash = hashlib.sha1(b"Hallomodel").hexdigest()
    expected_path = tmp_path / f"img_{expected_hash}.png"

    assert meta1["hash"] == expected_hash
    assert meta1["path"] == str(expected_path)
    assert meta1["path"] == meta2["path"]
    assert Path(meta1["path"]).read_bytes() == img_bytes
    assert len(calls) == 1
