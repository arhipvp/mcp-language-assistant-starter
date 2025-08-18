import os
import base64
from pathlib import Path

os.environ.setdefault("OPENROUTER_API_KEY","k")
os.environ.setdefault("OPENROUTER_TEXT_MODEL","m")
os.environ.setdefault("OPENROUTER_IMAGE_MODEL","m")
os.environ.setdefault("ANKI_DECK","d")
os.environ.setdefault("TELEGRAM_BOT_TOKEN","t")
os.environ.setdefault("GENAPI_API_KEY","g")

from app.mcp_tools import image_genapi


def _setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GENAPI_MODEL_ID", "model")
    monkeypatch.setenv("GENAPI_POLL_INTERVAL_MS", "10")
    monkeypatch.setenv("GENAPI_POLL_TIMEOUT_MS", "30")
    monkeypatch.setattr(image_genapi, "MEDIA_DIR", tmp_path)


def test_genapi_success_url(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_IS_SYNC", "true")

    img_bytes = b"url-bytes"

    def fake_create_generation_task(**kwargs):
        return {"result": {"images": [{"url": "http://example/img.png"}]}, "request_id": "1"}

    class DummyResp:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=None):
        return DummyResp(img_bytes)

    def fake_get_task_status(request_id):
        raise AssertionError("should not poll")

    monkeypatch.setattr(image_genapi, "create_generation_task", fake_create_generation_task)
    monkeypatch.setattr(image_genapi.requests, "get", fake_get)
    monkeypatch.setattr(image_genapi, "get_task_status", fake_get_task_status)

    path = image_genapi.generate_image_file_genapi("Hallo")
    p = Path(path)
    assert p.exists()
    assert p.read_bytes() == img_bytes


def test_genapi_success_b64(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_IS_SYNC", "true")

    img_bytes = b"b64-bytes"
    b64 = base64.b64encode(img_bytes).decode()

    def fake_create_generation_task(**kwargs):
        return {"result": {"images": [{"content": b64}]}}

    monkeypatch.setattr(image_genapi, "create_generation_task", fake_create_generation_task)
    monkeypatch.setattr(image_genapi, "get_task_status", lambda request_id: {})

    path = image_genapi.generate_image_file_genapi("Hallo")
    p = Path(path)
    assert p.exists()
    assert p.read_bytes() == img_bytes


def test_genapi_failure(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_IS_SYNC", "true")

    def fake_create_generation_task(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(image_genapi, "create_generation_task", fake_create_generation_task)

    path = image_genapi.generate_image_file_genapi("Hallo")
    assert path == ""
    assert list(tmp_path.iterdir()) == []


def test_genapi_unexpected_format(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_IS_SYNC", "true")

    def fake_create_generation_task(**kwargs):
        return {"result": {"foo": "bar"}}

    monkeypatch.setattr(image_genapi, "create_generation_task", fake_create_generation_task)
    monkeypatch.setattr(image_genapi, "get_task_status", lambda request_id: {})

    path = image_genapi.generate_image_file_genapi("Hallo")
    assert path == ""


def test_genapi_timeout(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_IS_SYNC", "false")

    def fake_create_generation_task(**kwargs):
        return {"request_id": "123"}

    calls = []

    def fake_get_task_status(request_id):
        calls.append(1)
        return {}

    class FakeTimer:
        def __init__(self):
            self.t = 0

        def time(self):
            return self.t

        def sleep(self, s):
            self.t += s

    fake = FakeTimer()

    monkeypatch.setattr(image_genapi, "create_generation_task", fake_create_generation_task)
    monkeypatch.setattr(image_genapi, "get_task_status", fake_get_task_status)
    monkeypatch.setattr(image_genapi.time, "time", fake.time)
    monkeypatch.setattr(image_genapi.time, "sleep", fake.sleep)

    path = image_genapi.generate_image_file_genapi("Hallo")
    assert path == ""
    assert calls  # ensure polling happened
