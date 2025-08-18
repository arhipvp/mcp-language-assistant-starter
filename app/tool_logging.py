from __future__ import annotations

import inspect
import logging
import time
import traceback
from functools import wraps
from typing import Any, Callable, Iterable

logger = logging.getLogger("mcp.tools")

_DEFAULT_SENSITIVE = {"token", "password", "secret", "api_key", "key"}


def _filter_args(bound: inspect.BoundArguments, sensitive: set[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for name, value in bound.arguments.items():
        lname = name.lower()
        if lname in sensitive or any(k in lname for k in sensitive):
            data[name] = "***"
        else:
            data[name] = value
    return data


def _log(name: str, status: str, start: float, filtered: dict[str, Any], err: str = "") -> None:
    """Helper to log execution info in a consistent format."""
    dur_ms = int((time.perf_counter() - start) * 1000)
    msg = f"{name} {status} {dur_ms}ms"
    if err:
        logger.warning("%s %s", msg, err)
        logger.debug("%s traceback:\n%s", name, traceback.format_exc())
    else:
        logger.info(msg)
    logger.debug("%s args=%s", name, filtered)


def log_tool(server: Any, name: str, *, sensitive_fields: Iterable[str] | None = None) -> Callable:
    """Decorator that registers a tool on ``server`` and logs its execution."""
    sensitive = {s.lower() for s in (sensitive_fields or [])} | _DEFAULT_SENSITIVE

    def decorator(func: Callable):
        is_coro = inspect.iscoroutinefunction(func)
        sig = inspect.signature(func)

        if is_coro:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                bound = sig.bind_partial(*args, **kwargs)
                filtered = _filter_args(bound, sensitive)
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    _log(name, "err", start, filtered, str(exc).splitlines()[0])
                    raise
                else:
                    _log(name, "ok", start, filtered)
                    return result
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                bound = sig.bind_partial(*args, **kwargs)
                filtered = _filter_args(bound, sensitive)
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    _log(name, "err", start, filtered, str(exc).splitlines()[0])
                    raise
                else:
                    _log(name, "ok", start, filtered)
                    return result

        return server.tool(name)(wrapper)

    return decorator
