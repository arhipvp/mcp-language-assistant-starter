import json
from pathlib import Path

from app.telemetry.jsonl import log_event


def read_events(base: Path):
    path = base / "var" / "telemetry" / "events.jsonl"
    lines = path.read_text().splitlines()
    return [json.loads(line) for line in lines]


def test_log_event_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("foo", {"a": 1})
    log_event("bar", {"b": 2})
    events = read_events(tmp_path)
    assert events == [
        {"name": "foo", "payload": {"a": 1}},
        {"name": "bar", "payload": {"b": 2}},
    ]


def test_log_event_filters(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = {
        "token": "secret",
        "Authorization": "Bearer x",
        "API_KEY": "top",
        "password": "p",
        "keep": 42,
    }
    log_event("secret", payload)
    events = read_events(tmp_path)
    assert events == [{"name": "secret", "payload": {"keep": 42}}]
