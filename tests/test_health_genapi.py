from types import SimpleNamespace

from app.mcp_tools import health_genapi


def _cfg():
    return SimpleNamespace(
        GENAPI_API_KEY="key",
        GENAPI_MODEL_ID="m",
        GENAPI_SIZE="1024x1024",
        GENAPI_QUALITY="low",
        GENAPI_BACKGROUND="transparent",
        GENAPI_CALLBACK_URL=None,
    )


def test_genapi_check_ok(monkeypatch):
    monkeypatch.setattr(health_genapi, "settings", _cfg())
    resp = type("R", (), {"status_code": 200, "text": "", "json": lambda self: {"id": "1"}})()
    monkeypatch.setattr(health_genapi.requests, "post", lambda *a, **k: resp)

    assert health_genapi.genapi_check() == {"ok": True, "id": "1"}


def test_genapi_check_error(monkeypatch):
    monkeypatch.setattr(health_genapi, "settings", _cfg())
    resp = type("R", (), {"status_code": 500, "text": "boom"})()
    monkeypatch.setattr(health_genapi.requests, "post", lambda *a, **k: resp)

    out = health_genapi.genapi_check()
    assert out["ok"] is False
    assert out["status"] == 500
