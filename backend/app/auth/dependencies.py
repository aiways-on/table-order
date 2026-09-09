"""FastAPI dependencies: authentication guards + context establishment.

`require_admin` reads the JWT from the HttpOnly cookie; `require_customer`
reads the session token header. Both set the request-scoped TenantContext so
downstream repositories are tenant-isolated. [SEC-08][SEC-12]
"""
from __future__ import annotations

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.orm import Session

from app.auth import security
from app.auth.service import AuthService
from app.core.context import Role, TenantContext, get_context, set_context
from app.core.database import get_db
from app.core.errors import UnauthorizedError

ADMIN_COOKIE = "access_token"
SESSION_HEADER = "X-Session-Token"


def client_ip(request: Request) -> str:
    """Best-effort client IP for rate-limit keying."""
    return request.client.host if request.client else "unknown"


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def require_admin(
    request: Request,
    access_token: str | None = Cookie(default=None),
) -> TenantContext:
    """Validate the admin JWT and establish an ADMIN context. [SEC-08]"""
    if not access_token:
        raise UnauthorizedError("Authentication required")
    claims = security.decode_admin_token(access_token)
    if claims is None or claims.get("role") != "admin":
        raise UnauthorizedError("Invalid or expired token")
    ctx = TenantContext(
        store_id=claims["sub"],
        role=Role.ADMIN,
        correlation_id=get_context().correlation_id,
    )
    set_context(ctx)
    return ctx


def require_customer(
    request: Request,
    x_session_token: str | None = Header(default=None),
    svc: AuthService = Depends(get_auth_service),
) -> TenantContext:
    """Validate the table session token and establish a CUSTOMER context."""
    if not x_session_token:
        raise UnauthorizedError("Session required")
    session = svc.verify_session(x_session_token)  # raises UnauthorizedError if invalid/expired
    ctx = TenantContext(
        store_id=session.store_id,
        role=Role.CUSTOMER,
        session_id=session.id,
        table_id=session.table_id,
        correlation_id=get_context().correlation_id,
    )
    set_context(ctx)
    return ctx
