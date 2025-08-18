import base64
from pathlib import Path
from types import SimpleNamespace

from app.mcp_tools import image


def _prepare(monkeypatch, tmp_path, sync=True):
    fake_settings = SimpleNamespace(
        GENAPI_API_KEY="key",
        GENAPI_MODEL_ID="m",
        GENAPI_SIZE="1024x1024",
        GENAPI_QUALITY="low",
        GENAPI_BACKGROUND="transparent",
        GENAPI_IS_SYNC=sync,
        GENAPI_CALLBACK_URL=None,
    )
    monkeypatch.setattr(image, "settings", fake_settings)
    monkeypatch.setattr(image, "MEDIA_DIR", tmp_path)


class DummyResp:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
        self.text = "" if isinstance(data, dict) else str(data)

    def json(self):
        if isinstance(self._data, Exception):
            raise self._data
        return self._data


def test_generate_image_b64(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    img_bytes = b"fake-bytes"
    b64 = base64.b64encode(img_bytes).decode()
    resp = DummyResp({"data": [{"b64_json": b64}]})
    monkeypatch.setattr(image.requests, "post", lambda *a, **k: resp)

    path = image.generate_image_file("Hallo")
    assert path.startswith("media/")
    p = tmp_path / Path(path).name
    assert p.exists()
    assert p.read_bytes() == img_bytes


def test_generate_image_async(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path, sync=False)
    resp = DummyResp({})
    monkeypatch.setattr(image.requests, "post", lambda *a, **k: resp)

    path = image.generate_image_file("Hallo")
    assert path == ""
    assert list(tmp_path.iterdir()) == []


def test_generate_image_error(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    resp = DummyResp(Exception("bad json"), status=500)
    resp.text = "oops"
    monkeypatch.setattr(image.requests, "post", lambda *a, **k: resp)

    path = image.generate_image_file("Hallo")
    assert path == ""
    assert list(tmp_path.iterdir()) == []

