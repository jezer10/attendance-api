import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Request


logger = logging.getLogger(__name__)
router = APIRouter()

SAFE_HEADER_WHITELIST = {"user-agent", "content-type", "x-request-id"}


@router.api_route(
    "",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    response_model=Dict[str, Any],
)
async def capture_test_event(request: Request) -> Dict[str, Any]:
    """Log the incoming request payload from repeated /test calls."""
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="ignore").strip()
    body: Any = None

    if body_text:
        try:
            body = json.loads(body_text)
        except json.JSONDecodeError:
            body = body_text

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() in SAFE_HEADER_WHITELIST
    }

    log_entry = {
        "method": request.method,
        "url": str(request.url),
        "query_params": dict(request.query_params),
        "client": request.client.host if request.client else None,
        "headers": headers,
        "body": body,
    }

    logger.info("Received /test request: %s", log_entry)
    return {"detail": "Evento registrado", "received": log_entry}
