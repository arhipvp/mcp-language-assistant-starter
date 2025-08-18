import importlib

from app.net.http import NetworkError


def load_health(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import app.settings as settings_module

    importlib.reload(settings_module)

    import app.tools.health as health_module

    importlib.reload(health_module)

    return health_module


def base_env():
    return {
        "OPENROUTER_TEXT_MODEL": "vendor/text-model",
        "ANKI_DECK": "deck",
        "TELEGRAM_BOT_TOKEN": "token",
        "ANKI_CONNECT_URL": "http://anki",
        "GENAPI_API_KEY": "sk-genapi",
        "GENAPI_MODEL_ID": "gen-model",
    }


def test_check_health_success(monkeypatch):
    env = base_env()
    env["OPENROUTER_API_KEY"] = "sk-or-v1-abc"
    health = load_health(monkeypatch, **env)

    def fake_request_json(method, url, json=None, headers=None, timeout=None):
        return {"result": 6}

    monkeypatch.setattr(health, "request_json", fake_request_json)

    assert health.check_health() == {
        "openrouter_text": {
            "ok": True,
            "model": env["OPENROUTER_TEXT_MODEL"],
            "error": None,
        },
        "genapi_image": {
            "ok": True,
            "model": env["GENAPI_MODEL_ID"],
            "error": None,
        },
        "anki": {"ok": True, "error": None},
    }


def test_check_health_anki_error(monkeypatch):
    env = base_env()
    env["OPENROUTER_API_KEY"] = "sk-or-v1-abc"
    health = load_health(monkeypatch, **env)

    def fake_request_json(*args, **kwargs):
        raise NetworkError("network", "boom")

    monkeypatch.setattr(health, "request_json", fake_request_json)

    result = health.check_health()

    assert result["anki"]["ok"] is False
    assert "boom" in result["anki"]["error"]


def test_check_health_invalid_openrouter(monkeypatch):
    env = base_env()
    env["OPENROUTER_API_KEY"] = "badkey"
    health = load_health(monkeypatch, **env)

    def fake_request_json(method, url, json=None, headers=None, timeout=None):
        return {"result": 6}

    monkeypatch.setattr(health, "request_json", fake_request_json)

    result = health.check_health()

    assert result["openrouter_text"]["ok"] is False
    assert result["openrouter_text"]["error"] == "invalid OPENROUTER_API_KEY"
    assert result["genapi_image"]["ok"] is True
    assert result["anki"]["ok"] is True

