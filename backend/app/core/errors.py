"""Domain error types + central exception handlers (fail-closed).  [SEC-03][SEC-15]

All errors are converted to generalized responses that never leak internal details
or stack traces; a correlation id is attached for traceability.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.context import get_context
from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base application error with an HTTP status and safe client message."""

    status_code = 500
    message = "Internal server error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message


class NotFoundError(AppError):
    status_code = 404
    message = "Not found"


class ForbiddenError(AppError):
    # 403 for authz failures. Cross-tenant access is generalized (no existence leak). [SEC-15]
    status_code = 403
    message = "Forbidden"


class UnauthorizedError(AppError):
    status_code = 401
    message = "Unauthorized"


class ValidationError(AppError):
    status_code = 422
    message = "Invalid request"


class RateLimitError(AppError):
    status_code = 429
    message = "Too many requests"


class ConflictError(AppError):
    status_code = 409
    message = "Conflict"


def _correlation_id() -> str | None:
    return get_context().correlation_id


def _error_body(status_code: int, message: str) -> dict:
    return {"error": {"status": status_code, "message": message, "correlation_id": _correlation_id()}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        # Client errors logged at info/warning; do not leak internals.
        # NB: `message` is the logger's positional arg — pass the client text as `detail`.
        logger.info("app_error", status=exc.status_code, detail=exc.message)
        return JSONResponse(status_code=exc.status_code, content=_error_body(exc.status_code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info("validation_error", errors=len(exc.errors()))
        return JSONResponse(status_code=422, content=_error_body(422, "Invalid request"))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Fail closed: log full detail server-side, return generic message. [SEC-15]
        logger.error("unhandled_exception", error_type=type(exc).__name__)
        return JSONResponse(status_code=500, content=_error_body(500, "Internal server error"))
