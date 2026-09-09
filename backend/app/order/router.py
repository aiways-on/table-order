"""Order + session-lifecycle + SSE HTTP endpoints.

Access: customer (session token header) confirms/lists own orders; admin (JWT
cookie) monitors the store, changes status, deletes, closes sessions, reads
history. Detail is readable by either (customer only for their own session).
[SEC-08] BR-O09/O13/O14

Threadpool note (same as menu): sync path operations and their sync dependencies
run in separate threadpool workers, each with its own copy of the request
contextvars. A TenantContext set inside a guard is therefore NOT visible in the
endpoint's thread where the repository reads it — so each sync endpoint
re-asserts the context (returned by the guard) before touching the service.

SSE endpoints are async (run on the event loop) and authenticate from the token
directly; they do not touch the tenant-scoped repository. [NFR-P2]
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, Header, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import security
from app.auth.dependencies import require_admin, require_customer
from app.auth.service import AuthService
from app.core.context import Role, TenantContext, get_context, set_context
from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.core.events import event_bus
from app.order import events
from app.order.schemas import HistoryOut, OrderCreate, OrderOut, StatusUpdate
from app.order.service import OrderService
from app.order.sse import SSE_HEADERS, event_stream
from app.shared.models import OrderStatus

router = APIRouter(tags=["order"])


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db)


def require_order_viewer(
    access_token: str | None = Cookie(default=None),
    x_session_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> TenantContext:
    """Admin (cookie) OR active customer session (header) may read a detail. BR-O14"""
    if access_token:
        claims = security.decode_admin_token(access_token)
        if claims and claims.get("role") == "admin":
            ctx = TenantContext(
                store_id=claims["sub"], role=Role.ADMIN, correlation_id=get_context().correlation_id
            )
            set_context(ctx)
            return ctx
    if x_session_token:
        session = AuthService(db).verify_session(x_session_token)
        ctx = TenantContext(
            store_id=session.store_id,
            role=Role.CUSTOMER,
            session_id=session.id,
            table_id=session.table_id,
            correlation_id=get_context().correlation_id,
        )
        set_context(ctx)
        return ctx
    raise UnauthorizedError("Authentication required")


def _publish(store_id: str, session_id: str, data: dict) -> None:
    """Publish to store + session topics (thread-safe from sync path). BR-O12"""
    event_bus.publish_sync(events.store_topic(store_id), data)
    event_bus.publish_sync(events.session_topic(session_id), data)


# --- customer: confirm / list own session ------------------------------

@router.post("/api/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_customer),
) -> OrderOut:
    set_context(ctx)
    out = svc.create(ctx, body)
    db.commit()  # SSE only after commit [BR-O06]
    _publish(ctx.store_id, out.session_id, events.order_created_event(out))
    return out


@router.get("/api/orders", response_model=list[OrderOut])
def list_my_orders(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_customer),
) -> list[OrderOut]:
    set_context(ctx)
    return svc.list_session(ctx, limit=limit, offset=offset)


# --- admin: monitoring / detail -----------------------------------------

@router.get("/api/orders/store", response_model=list[OrderOut])
def list_store_orders(
    table_id: str | None = Query(default=None),
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_admin),
) -> list[OrderOut]:
    set_context(ctx)
    return svc.list_store(table_id=table_id, status=order_status)


# --- SSE (declared before /{order_id} so literals win the route match) --

@router.get("/api/orders/stream")
async def stream_store_orders(access_token: str | None = Cookie(default=None)) -> StreamingResponse:
    """Admin store-wide SSE (JWT cookie). US-ORDER-09"""
    if not access_token:
        raise UnauthorizedError("Authentication required")
    claims = security.decode_admin_token(access_token)
    if claims is None or claims.get("role") != "admin":
        raise UnauthorizedError("Invalid or expired token")
    topic = events.store_topic(claims["sub"])
    return StreamingResponse(event_stream(topic), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/api/orders/session/stream")
async def stream_session_orders(
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Customer session SSE. EventSource cannot set headers, so the session
    token is passed as ?token= (TLS-only in prod; local HTTP allowed). US-ORDER-08 [SEC-04]

    Single-instance tradeoff: the request's DB session is held for the stream's
    lifetime. For horizontal scale, move fan-out to Redis pub/sub (RES-08).
    """
    if not token:
        raise UnauthorizedError("Session required")
    session = AuthService(db).verify_session(token)  # raises if invalid/expired
    topic = events.session_topic(session.id)
    return StreamingResponse(event_stream(topic), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_order_viewer),
) -> OrderOut:
    set_context(ctx)
    return svc.get(order_id, ctx)


@router.patch("/api/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_admin),
) -> OrderOut:
    set_context(ctx)
    out = svc.update_status(order_id, body.status)
    db.commit()
    _publish(ctx.store_id, out.session_id, events.order_status_event(out))
    return out


@router.delete("/api/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_admin),
) -> Response:
    set_context(ctx)
    out = svc.delete(order_id)
    db.commit()
    _publish(ctx.store_id, out.session_id, events.order_deleted_event(out))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- admin: session close → history / history query ---------------------

@router.post("/api/sessions/{session_id}/close", status_code=status.HTTP_204_NO_CONTENT)
def close_session(
    session_id: str,
    db: Session = Depends(get_db),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_admin),
) -> Response:
    set_context(ctx)
    _sid, table_id = svc.close_session(session_id)
    db.commit()
    _publish(ctx.store_id, session_id, events.session_closed_event(session_id, table_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/history", response_model=list[HistoryOut])
def list_history(
    table_id: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    svc: OrderService = Depends(get_order_service),
    ctx: TenantContext = Depends(require_admin),
) -> list[HistoryOut]:
    set_context(ctx)
    return svc.list_history(table_id=table_id, date_from=date_from, date_to=date_to)
