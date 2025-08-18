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
                logger.info("%s start %s", name, filtered)
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    dur = time.perf_counter() - start
                    logger.info("%s ok %.3fs", name, dur)
                    logger.debug("%s result=%s", name, result)
                    return result
                except Exception as exc:  # noqa: BLE001
                    dur = time.perf_counter() - start
                    logger.warning("%s err %s %.3fs", name, exc, dur)
                    logger.debug("%s traceback:\n%s", name, traceback.format_exc())
                    raise
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                bound = sig.bind_partial(*args, **kwargs)
                filtered = _filter_args(bound, sensitive)
                logger.info("%s start %s", name, filtered)
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    dur = time.perf_counter() - start
                    logger.info("%s ok %.3fs", name, dur)
                    logger.debug("%s result=%s", name, result)
                    return result
                except Exception as exc:  # noqa: BLE001
                    dur = time.perf_counter() - start
                    logger.warning("%s err %s %.3fs", name, exc, dur)
                    logger.debug("%s traceback:\n%s", name, traceback.format_exc())
                    raise

        return server.tool(name)(wrapper)

    return decorator
