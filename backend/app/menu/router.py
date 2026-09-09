"""Menu HTTP endpoints.  Read: customer|admin. Write: admin-only. [SEC-08] BR-M08"""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import security
from app.auth.dependencies import get_auth_service, require_admin
from app.auth.service import AuthService
from app.core.context import Role, TenantContext, get_context, set_context
from app.core.database import get_db
from app.core.errors import UnauthorizedError
from app.menu.schemas import (
    MenuCreate,
    MenuGroupedResponse,
    MenuOut,
    MenuUpdate,
    ReorderRequest,
    ReorderResponse,
)
from app.menu.service import MenuService

# NOTE: sync path operations and their sync dependencies run in separate
# threadpool workers, each with its OWN copy of the request contextvars. A
# TenantContext set inside a guard is therefore NOT visible to the endpoint's
# thread, where MenuRepository reads it. So each endpoint re-asserts the context
# (returned by the guard) in its own thread before touching the service.
router = APIRouter(prefix="/api/menus", tags=["menu"])


def get_menu_service(db: Session = Depends(get_db)) -> MenuService:
    return MenuService(db)


def require_viewer(
    request: Request,
    access_token: str | None = Cookie(default=None),
    x_session_token: str | None = Header(default=None),
    svc: AuthService = Depends(get_auth_service),
) -> TenantContext:
    """Allow either an authenticated admin (JWT cookie) or an active customer
    session (token header) to read menus, establishing the tenant context. BR-M08
    """
    if access_token:
        claims = security.decode_admin_token(access_token)
        if claims and claims.get("role") == "admin":
            ctx = TenantContext(
                store_id=claims["sub"], role=Role.ADMIN, correlation_id=get_context().correlation_id
            )
            set_context(ctx)
            return ctx
    if x_session_token:
        session = svc.verify_session(x_session_token)  # raises if invalid/expired
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


# --- read (customer | admin) -------------------------------------------

@router.get("", response_model=MenuGroupedResponse)
def list_menus(
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_viewer),
) -> MenuGroupedResponse:
    set_context(ctx)  # re-assert in the endpoint's own thread [see note below]
    return svc.list_grouped()


@router.get("/flat", response_model=list[MenuOut])
def list_menus_flat(
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_viewer),
) -> list[MenuOut]:
    set_context(ctx)
    return svc.list_flat()


@router.get("/{menu_id}", response_model=MenuOut)
def get_menu(
    menu_id: str,
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_viewer),
) -> MenuOut:
    set_context(ctx)
    return svc.get(menu_id)


# --- write (admin only) -------------------------------------------------

@router.post("", response_model=MenuOut, status_code=status.HTTP_201_CREATED)
def create_menu(
    body: MenuCreate,
    db: Session = Depends(get_db),
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_admin),
) -> MenuOut:
    set_context(ctx)
    out = svc.create(body)
    db.commit()
    return out


@router.put("/{menu_id}", response_model=MenuOut)
def update_menu(
    menu_id: str,
    body: MenuUpdate,
    db: Session = Depends(get_db),
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_admin),
) -> MenuOut:
    set_context(ctx)
    out = svc.update(menu_id, body)
    db.commit()
    return out


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_admin),
) -> Response:
    set_context(ctx)
    svc.delete(menu_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reorder", response_model=ReorderResponse)
def reorder_menus(
    body: ReorderRequest,
    db: Session = Depends(get_db),
    svc: MenuService = Depends(get_menu_service),
    ctx: TenantContext = Depends(require_admin),
) -> ReorderResponse:
    set_context(ctx)
    updated = svc.reorder(body.menu_ids)
    db.commit()
    return ReorderResponse(updated=updated)
