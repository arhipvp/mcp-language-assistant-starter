import logging
import time
from typing import Any, Dict, Optional

import requests

__all__ = [
    "GenAPIClient",
    "GenAPIError",
    "GenAPIBadRequest",
    "GenAPIUnauthorized",
    "GenAPIPaymentRequired",
    "GenAPINotFound",
    "GenAPISessionExpired",
    "GenAPIServiceUnavailable",
    "GenAPITaskFailed",
]

logger = logging.getLogger(__name__)


class GenAPIError(Exception):
    """Base exception for GenAPI errors."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class GenAPIBadRequest(GenAPIError):
    pass


class GenAPIUnauthorized(GenAPIError):
    pass


class GenAPIPaymentRequired(GenAPIError):
    pass


class GenAPINotFound(GenAPIError):
    pass


class GenAPISessionExpired(GenAPIError):
    pass


class GenAPIServiceUnavailable(GenAPIError):
    pass


class GenAPITaskFailed(GenAPIError):
    pass


_ERROR_MAP = {
    400: GenAPIBadRequest,
    401: GenAPIUnauthorized,
    402: GenAPIPaymentRequired,
    404: GenAPINotFound,
    419: GenAPISessionExpired,
    503: GenAPIServiceUnavailable,
}


def _extract_details(response: requests.Response) -> Dict[str, Any]:
    try:
        return response.json()  # type: ignore[return-value]
    except ValueError:
        return {"text": response.text}


class GenAPIClient:
    """Low-level HTTP client for GenAPI."""

    BASE_URL = "https://gen-api.ru"
    NETWORKS_PATH = "/api/v1/networks/{model_id}"
    REQUESTS_PATH = "/api/v1/requests/{request_id}"

    def __init__(self, token: str, *, timeout: int = 30, retries: int = 3) -> None:
        self.token = token
        self.timeout = timeout
        self.retries = retries

    @property
    def base_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def create_generation_task(
        self,
        model_id: str,
        prompt: str,
        is_sync: bool,
        callback_url: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{self.NETWORKS_PATH.format(model_id=model_id)}"
        payload: Dict[str, Any] = {"prompt": prompt, "is_sync": is_sync}
        if callback_url:
            payload["callback_url"] = callback_url
        if extra:
            payload.update(extra)

        response = requests.post(url, json=payload, headers=self.base_headers, timeout=self.timeout)
        if response.status_code in _ERROR_MAP:
            raise _ERROR_MAP[response.status_code](
                "HTTP error",
                status_code=response.status_code,
                details=_extract_details(response),
            )
        response.raise_for_status()
        data = response.json()
        request_id = data.get("request_id")
        if request_id:
            logger.info("Created generation task", extra={"request_id": request_id})
        return data

    def get_task_status(self, request_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{self.REQUESTS_PATH.format(request_id=request_id)}"
        headers = self.base_headers
        attempt = 0
        while True:
            attempt += 1
            try:
                logger.debug("Checking task status", extra={"request_id": request_id, "attempt": attempt})
                response = requests.get(url, headers=headers, timeout=self.timeout)
            except (requests.Timeout, requests.RequestException) as exc:
                if attempt >= self.retries:
                    raise GenAPIError(str(exc)) from exc
                time.sleep(1 * (2 ** (attempt - 1)))
                continue

            if response.status_code in _ERROR_MAP:
                raise _ERROR_MAP[response.status_code](
                    "HTTP error",
                    status_code=response.status_code,
                    details=_extract_details(response),
                )
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status == "processing":
                time.sleep(1)
                continue
            if status == "failed":
                raise GenAPITaskFailed("Task failed", details=data)
            if status == "success":
                logger.info("Task completed", extra={"request_id": request_id})
                return data
            raise GenAPIError(f"Unknown status: {status}", details=data)
