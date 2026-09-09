"""Per-request tenant context (store_id / role / session).  [SEC-08]

Propagated via ContextVar so repositories can enforce tenant scoping without
threading the context through every call site.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    ANONYMOUS = "anonymous"


@dataclass(frozen=True)
class TenantContext:
    """Identity established by the auth middleware for the current request."""

    store_id: str | None = None
    role: Role = Role.ANONYMOUS
    session_id: str | None = None
    table_id: str | None = None
    correlation_id: str | None = None


_ANONYMOUS = TenantContext()
_current: ContextVar[TenantContext] = ContextVar("tenant_context", default=_ANONYMOUS)


def set_context(ctx: TenantContext) -> None:
    _current.set(ctx)


def get_context() -> TenantContext:
    return _current.get()


def reset_context() -> None:
    _current.set(_ANONYMOUS)


def require_store_id() -> str:
    """Return the current store_id or fail closed if absent.  [SEC-15]"""
    store_id = _current.get().store_id
    if not store_id:
        from app.core.errors import ForbiddenError

        raise ForbiddenError("No tenant context")
    return store_id
