import importlib
import pytest


_BASE_ENV = {
    "OPENROUTER_API_KEY": "k",
    "OPENROUTER_TEXT_MODEL": "t",
    "ANKI_DECK": "d",
    "TELEGRAM_BOT_TOKEN": "x",
    "GENAPI_API_KEY": "g",
}


def _load(monkeypatch, quality: str | None):
    for key, val in _BASE_ENV.items():
        monkeypatch.setenv(key, val)
    if quality is None:
        monkeypatch.delenv("GENAPI_QUALITY", raising=False)
    else:
        monkeypatch.setenv("GENAPI_QUALITY", quality)
    import app.settings as settings_module
    return importlib.reload(settings_module)


def test_valid_values(monkeypatch):
    for q in ("high", "medium", "low"):
        settings_module = _load(monkeypatch, q)
        assert settings_module.settings.GENAPI_QUALITY == q


def test_invalid_values(monkeypatch):
    for q in ("h", "med", "LOWER", "123"):
        with pytest.raises(RuntimeError):
            _load(monkeypatch, q)


def test_default_and_normalization(monkeypatch):
    mod = _load(monkeypatch, None)
    assert mod.settings.GENAPI_QUALITY == "high"
    mod = _load(monkeypatch, "")
    assert mod.settings.GENAPI_QUALITY == "high"
    mod = _load(monkeypatch, "HIGH")
    assert mod.settings.GENAPI_QUALITY == "high"

