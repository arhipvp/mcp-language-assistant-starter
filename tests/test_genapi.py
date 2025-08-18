import importlib
import logging
import sys

import pytest

from app.net.http import NetworkError


def import_genapi(monkeypatch, api_key="key", model_id="m"):
    if api_key is None:
        monkeypatch.delenv("GENAPI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GENAPI_API_KEY", api_key)
    if model_id is None:
        monkeypatch.delenv("GENAPI_MODEL_ID", raising=False)
    else:
        monkeypatch.setenv("GENAPI_MODEL_ID", model_id)
    sys.modules.pop("app.net.genapi", None)
    return importlib.import_module("app.net.genapi")


def test_missing_api_key(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR, logger="app.net.genapi"):
        with pytest.raises(RuntimeError, match="GENAPI_API_KEY is missing"):
            import_genapi(monkeypatch, api_key=None)
    assert any(r.message == "GENAPI_API_KEY is missing" for r in caplog.records)


def test_missing_model_id(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR, logger="app.net.genapi"):
        with pytest.raises(RuntimeError, match="GENAPI_MODEL_ID is missing"):
            import_genapi(monkeypatch, model_id="")
    assert any(r.message == "GENAPI_MODEL_ID is missing" for r in caplog.records)


@pytest.mark.parametrize(
    "code,message",
    [
        (401, "Auth failed: check GENAPI_API_KEY or maintenance"),
        (402, "Insufficient balance"),
        (404, "Unknown model id"),
        (419, "Rate limit"),
        (503, "GenAPI temporary error"),
    ],
)

def test_error_mapping(monkeypatch, caplog, code, message):
    mod = import_genapi(monkeypatch)

    def fake_request(method, url, json=None, headers=None, timeout=None):
        raise NetworkError(code, "HTTP error")

    monkeypatch.setattr(mod, "request_json", fake_request)

    with caplog.at_level(logging.ERROR, logger="app.net.genapi"):
        with pytest.raises(NetworkError) as exc:
            mod.request_genapi({})
    assert exc.value.code == code
    assert exc.value.message == message
    assert any(r.message == message for r in caplog.records)
