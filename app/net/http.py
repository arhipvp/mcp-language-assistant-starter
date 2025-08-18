import time
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests


class NetworkError(Exception):
    """Standard network error with structured details."""

    def __init__(self, code: Any, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"NetworkError(code={self.code!r}, message={self.message!r}, details={self.details!r})"


def request_json(
    method: str,
    url: str,
    *,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    retries: int = 3,
    provider: Optional[str] = None,
    backoff_base: float = 1,
) -> Dict[str, Any]:
    """Perform an HTTP request expecting JSON with retries and exponential backoff."""
    provider = provider or urlparse(url).netloc
    logger = logging.getLogger(__name__)

    last_error: Optional[NetworkError] = None
    for attempt in range(1, retries + 1):
        start = time.perf_counter()
        try:
            resp = requests.request(
                method, url, json=json, headers=headers, timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()
            lat_ms = int((time.perf_counter() - start) * 1000)
            finish = None
            if isinstance(data, dict):
                finish = data.get("finish_reason")
                if not finish and isinstance(data.get("choices"), list):
                    first = data["choices"][0]
                    if isinstance(first, dict):
                        finish = first.get("finish_reason")
            logger.info(
                "request",
                extra={
                    "step": "net.http",
                    "provider": provider,
                    "attempt": attempt,
                    "lat_ms": lat_ms,
                    "status_code": resp.status_code,
                    "finish_reason": finish or "-",
                },
            )
            return data
        except requests.HTTPError as exc:  # noqa: PERF203
            response = exc.response
            details = {
                "status_code": getattr(response, "status_code", None),
                "text": getattr(response, "text", ""),
            }
            last_error = NetworkError(details["status_code"], "HTTP error", details)
            level = logging.WARNING if attempt < retries else logging.ERROR
            lat_ms = int((time.perf_counter() - start) * 1000)
            logger.log(
                level,
                "request error",
                extra={
                    "step": "net.http",
                    "provider": provider,
                    "attempt": attempt,
                    "lat_ms": lat_ms,
                    "status_code": details["status_code"],
                },
                exc_info=level == logging.ERROR,
            )
        except requests.RequestException as exc:  # network issue/timeout
            last_error = NetworkError("network", str(exc))
            level = logging.WARNING if attempt < retries else logging.ERROR
            lat_ms = int((time.perf_counter() - start) * 1000)
            logger.log(
                level,
                "request error",
                extra={
                    "step": "net.http",
                    "provider": provider,
                    "attempt": attempt,
                    "lat_ms": lat_ms,
                },
                exc_info=level == logging.ERROR,
            )
        except ValueError as exc:  # JSON decoding
            last_error = NetworkError("json", str(exc))
            level = logging.WARNING if attempt < retries else logging.ERROR
            lat_ms = int((time.perf_counter() - start) * 1000)
            logger.log(
                level,
                "request error",
                extra={
                    "step": "net.http",
                    "provider": provider,
                    "attempt": attempt,
                    "lat_ms": lat_ms,
                },
                exc_info=level == logging.ERROR,
            )

        if attempt == retries:
            break
        time.sleep(backoff_base * (2 ** (attempt - 1)))

    assert last_error is not None  # for mypy
    raise last_error
