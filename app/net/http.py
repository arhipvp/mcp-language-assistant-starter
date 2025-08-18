import time
from typing import Any, Dict, Optional

import requests


class NetworkError(RuntimeError):
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
    backoff_base: float = 1,
) -> Dict[str, Any]:
    """Perform an HTTP request expecting JSON with retries and exponential backoff."""

    last_error: Optional[NetworkError] = None
    for attempt in range(retries):
        try:
            resp = requests.request(
                method, url, json=json, headers=headers, timeout=timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as exc:  # noqa: PERF203
            response = exc.response
            details = {
                "status_code": getattr(response, "status_code", None),
                "text": getattr(response, "text", ""),
            }
            last_error = NetworkError(details["status_code"], "HTTP error", details)
        except requests.RequestException as exc:  # network issue/timeout
            last_error = NetworkError("network", str(exc))
        except ValueError as exc:  # JSON decoding
            last_error = NetworkError("json", str(exc))

        if attempt == retries - 1:
            break
        time.sleep(backoff_base * (2**attempt))

    assert last_error is not None  # for mypy
    raise last_error
