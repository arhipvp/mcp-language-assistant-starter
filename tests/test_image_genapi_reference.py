import os
import base64
from pathlib import Path
from io import BytesIO
import builtins

import pytest

# required settings for importing modules
os.environ.setdefault("OPENROUTER_API_KEY", "k")
os.environ.setdefault("OPENROUTER_TEXT_MODEL", "m")
os.environ.setdefault("OPENROUTER_IMAGE_MODEL", "m")
os.environ.setdefault("ANKI_DECK", "d")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "t")
os.environ.setdefault("GENAPI_API_KEY", "g")

from app.mcp_tools import image_genapi


def _setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GENAPI_MODEL_ID", "model")
    monkeypatch.setenv("GENAPI_POLL_INTERVAL_MS", "10")
    monkeypatch.setenv("GENAPI_POLL_TIMEOUT_MS", "30")
    monkeypatch.setenv("GENAPI_IS_SYNC", "true")
    monkeypatch.setattr(image_genapi, "MEDIA_DIR", tmp_path)


def _dummy_resp_bytes() -> bytes:
    return b"result-bytes"


def _fake_create(monkeypatch, out, recorder):
    def fake_create_generation_task(**kwargs):
        recorder.update(kwargs)
        return {"result": {"images": [{"content": base64.b64encode(out).decode()}]}}

    monkeypatch.setattr(image_genapi, "create_generation_task", fake_create_generation_task)
    monkeypatch.setattr(image_genapi, "get_task_status", lambda request_id: {})


def test_no_reference(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    recorder = {}
    _fake_create(monkeypatch, _dummy_resp_bytes(), recorder)

    path = image_genapi.generate_image_file_genapi("Hallo")
    assert Path(path).exists()
    assert "image_url" not in recorder and "image_path" not in recorder and "image_b64" not in recorder


def test_reference_url(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    recorder = {}
    _fake_create(monkeypatch, _dummy_resp_bytes(), recorder)

    url = "https://example.com/ref.png"
    path = image_genapi.generate_image_file_genapi("Hallo", ref_image=url)
    assert Path(path).exists()
    assert recorder["image_url"] == url


def test_reference_path(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    recorder = {}
    _fake_create(monkeypatch, _dummy_resp_bytes(), recorder)
    monkeypatch.setenv("GENAPI_ALLOWED_IMAGE_TYPES", "image/png")

    img = b"\x89PNG\r\n\x1a\n1234"
    fake_path = "/tmp/ref.bin"
    monkeypatch.setattr(os.path, "isfile", lambda p: p == fake_path)
    monkeypatch.setattr(os.path, "getsize", lambda p: len(img))

    def fake_open(p, mode="rb"):
        assert p == fake_path
        return BytesIO(img)

    monkeypatch.setattr(builtins, "open", fake_open)

    path = image_genapi.generate_image_file_genapi("Hallo", ref_image=fake_path)
    assert Path(path).exists()
    assert recorder["image_path"] == fake_path


def test_reference_bytes(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    recorder = {}
    _fake_create(monkeypatch, _dummy_resp_bytes(), recorder)
    monkeypatch.setenv("GENAPI_ALLOWED_IMAGE_TYPES", "image/png")

    img = b"\x89PNG\r\n\x1a\n1234"
    path = image_genapi.generate_image_file_genapi("Hallo", ref_image=img)
    assert Path(path).exists()
    expected = base64.b64encode(img).decode()
    assert recorder["image_b64"] == expected


def test_quality_param(monkeypatch, tmp_path):
    _setup_env(monkeypatch, tmp_path)
    recorder = {}
    _fake_create(monkeypatch, _dummy_resp_bytes(), recorder)
    monkeypatch.setattr(
        image_genapi, "settings", type("S", (), {"GENAPI_QUALITY": "medium"})()
    )
    path = image_genapi.generate_image_file_genapi("Hallo")
    assert Path(path).exists()
    assert recorder["quality"] == "medium"


def test_reference_size_limit(monkeypatch, tmp_path, caplog):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_ALLOWED_IMAGE_TYPES", "image/png")
    monkeypatch.setenv("GENAPI_REF_IMAGE_MAX_BYTES", "4")
    called = {}

    def fail_create(**kwargs):
        called["x"] = True
        raise AssertionError("should not be called")

    monkeypatch.setattr(image_genapi, "create_generation_task", fail_create)
    monkeypatch.setattr(image_genapi, "get_task_status", lambda request_id: {})

    img = b"\x89PNG\r\n\x1a\n1234"
    with caplog.at_level("WARNING", logger=image_genapi.__name__):
        result = image_genapi.generate_image_file_genapi("Hallo", ref_image=img)
    assert result == ""
    assert not called
    assert any("too large" in r.getMessage() for r in caplog.records)


def test_reference_bad_mime(monkeypatch, tmp_path, caplog):
    _setup_env(monkeypatch, tmp_path)
    monkeypatch.setenv("GENAPI_ALLOWED_IMAGE_TYPES", "image/jpeg")
    called = {}

    def fail_create(**kwargs):
        called["x"] = True
        raise AssertionError("should not be called")

    monkeypatch.setattr(image_genapi, "create_generation_task", fail_create)
    monkeypatch.setattr(image_genapi, "get_task_status", lambda request_id: {})

    img = b"\x89PNG\r\n\x1a\n1234"
    with caplog.at_level("WARNING", logger=image_genapi.__name__):
        result = image_genapi.generate_image_file_genapi("Hallo", ref_image=img)
    assert result == ""
    assert not called
    assert any("Unsupported" in r.getMessage() for r in caplog.records)
