from __future__ import annotations

import logging
import os
from typing import Any, Dict

from .http import NetworkError, request_json

logger = logging.getLogger(__name__)

API_URL = "https://gen-api.ru/v1/chat"

API_KEY = os.environ.get("GENAPI_API_KEY")
MODEL_ID = os.environ.get("GENAPI_MODEL_ID")

if not API_KEY:
    logger.error("GENAPI_API_KEY is missing")
    raise RuntimeError("GENAPI_API_KEY is missing")
if not MODEL_ID:
    logger.error("GENAPI_MODEL_ID is missing")
    raise RuntimeError("GENAPI_MODEL_ID is missing")

_ERROR_MESSAGES = {
    401: "Auth failed: check GENAPI_API_KEY or maintenance",
    402: "Insufficient balance",
    404: "Unknown model id",
    419: "Rate limit",
    503: "GenAPI temporary error",
}


def request_genapi(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        return request_json("POST", API_URL, json=payload, headers=headers, timeout=30)
    except NetworkError as exc:
        message = _ERROR_MESSAGES.get(exc.code)
        if message:
            logger.error(message)
            raise NetworkError(exc.code, message, exc.details) from None
        raise
