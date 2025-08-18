import base64
from pathlib import Path
from types import SimpleNamespace

from app.mcp_tools import image


def _prepare(monkeypatch, tmp_path):
    fake_settings = SimpleNamespace(
        OPENROUTER_API_KEY="key", OPENROUTER_IMAGE_MODEL="model"
    )
    monkeypatch.setattr(image, "settings", fake_settings)
    monkeypatch.setattr(image, "MEDIA_DIR", tmp_path)
    monkeypatch.setattr(image.time, "time", lambda: 1)


def test_generate_image_b64(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    img_bytes = b"fake-bytes"
    b64 = base64.b64encode(img_bytes).decode()

    def fake_request_json(method, url, headers=None, json=None, timeout=None):
        return {"data": [{"b64_json": b64}]}

    monkeypatch.setattr(image, "request_json", fake_request_json)

    path = image.generate_image_file("Hallo")
    p = Path(path)
    assert p.exists()
    assert p.read_bytes() == img_bytes


def test_generate_image_url(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    img_bytes = b"url-bytes"

    def fake_request_json(method, url, headers=None, json=None, timeout=None):
        return {"data": [{"url": "http://example.com/img.png"}]}

    class DummyResp:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=None):
        return DummyResp(img_bytes)

    monkeypatch.setattr(image, "request_json", fake_request_json)
    monkeypatch.setattr(image.requests, "get", fake_get)

    path = image.generate_image_file("Hallo")
    p = Path(path)
    assert p.exists()
    assert p.read_bytes() == img_bytes


def test_generate_image_failure(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)

    def fake_request_json(method, url, headers=None, json=None, timeout=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(image, "request_json", fake_request_json)

    path = image.generate_image_file("Hallo")
    assert path == ""
    assert list(tmp_path.iterdir()) == []
