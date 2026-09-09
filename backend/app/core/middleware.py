"""HTTP middleware: correlation id + security headers.  [SEC-04]

Ordering (outermost first): CorrelationId -> SecurityHeaders.
Authentication/authorization middleware is added by the auth unit (U2) and runs after these.
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.context import TenantContext, get_context, set_context
from app.core.metrics import metrics

_CORRELATION_HEADER = "X-Correlation-ID"

# [SEC-04] Security headers applied to every response.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'",
    # HSTS is meaningful only over HTTPS; harmless header for prod termination. [SEC-04]
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get(_CORRELATION_HEADER) or str(uuid.uuid4())
        # Seed a fresh anonymous context carrying the correlation id.
        base = get_context()
        set_context(TenantContext(correlation_id=cid, store_id=base.store_id, role=base.role))
        start = _now()
        try:
            response = await call_next(request)
        finally:
            metrics.observe_request(request.url.path, _now() - start)
        response.headers[_CORRELATION_HEADER] = cid
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response


def _now() -> float:
    import time

    return time.monotonic()
