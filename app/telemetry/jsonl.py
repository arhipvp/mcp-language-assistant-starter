import json
from pathlib import Path
from typing import Any


_SENSITIVE_KEYS = {"api_key", "token", "authorization", "password"}


def _filter_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive keys from payload (case-insensitive)."""
    return {k: v for k, v in payload.items() if k.lower() not in _SENSITIVE_KEYS}


def log_event(name: str, payload: dict) -> None:
    """Append a telemetry event as JSON line.

    Args:
        name: Event name.
        payload: Event payload dictionary.
    """
    path = Path("var/telemetry/events.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"name": name, "payload": _filter_payload(payload)}
    with path.open("a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")
