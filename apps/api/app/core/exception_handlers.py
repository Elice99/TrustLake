"""
Global exception handlers — every error response, from any route,
follows the same {"error": {"code", "message", "details"}} envelope
per the architecture doc's API design requirement. Without this,
FastAPI's defaults are inconsistent: HTTPException gives
{"detail": "..."}, validation errors give a different shape again,
and anything unhandled leaks a raw "Internal Server Error" with no
useful information — which is exactly what happened when
python-multipart was missing and when the users table didn't
exist yet (the empty-DB incident) — both surfaced as an opaque 500
with nothing to go on.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.services.storage import StorageError

logger = logging.getLogger("trustlake.api")


def _envelope(code: str, message: str, details: object = None) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "details": details}}


# Python's own phrase text for a few status codes has changed between
# versions, which would silently change the "code" clients see. Pin the
# ones we emit so the API contract stays stable everywhere.
_CODE_OVERRIDES = {413: "payload_too_large"}


def _slug(status_code: int) -> str:
    """401 -> "unauthorized", 404 -> "not_found", etc."""
    if status_code in _CODE_OVERRIDES:
        return _CODE_OVERRIDES[status_code]
    try:
        return HTTPStatus(status_code).phrase.lower().replace(" ", "_")
    except ValueError:
        return "error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Covers every deliberate HTTPException raised anywhere — our
        own route code, and FastAPI's own internals (e.g. the
        "Not authenticated" error OAuth2PasswordBearer raises when a
        request has no token at all)."""
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(_slug(exc.status_code), str(exc.detail)),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Pydantic request-validation failures (e.g. a malformed email
        in a register request) — FastAPI's default shape for these is
        different from HTTPException's, so it needs its own handler to
        land in the same envelope."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope(
                "validation_error", "Request validation failed", exc.errors()
            ),
        )

    @app.exception_handler(StorageError)
    async def handle_storage_error(request: Request, exc: StorageError) -> JSONResponse:
        """Object storage is down or misconfigured. A dependency being
        unavailable is a 503, not a generic 500. The detail is logged
        server-side; the client only gets a generic message."""
        logger.error("Storage failure on %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_envelope(
                "storage_unavailable", "Object storage is currently unavailable"
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catches anything not already handled above — a real bug, a
        database being unreachable, anything. Logs the full traceback
        server-side (so it's still debuggable) but returns only a
        generic message to the client — never the exception text,
        which could leak internal details (table names, file paths,
        library versions) to whoever sent the request."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("internal_server_error", "An unexpected error occurred"),
        )
