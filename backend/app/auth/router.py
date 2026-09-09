"""Auth & session HTTP endpoints.  [SEC-08][SEC-11][SEC-12]"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    ADMIN_COOKIE,
    client_ip,
    get_auth_service,
    require_admin,
    require_customer,
)
from app.auth.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    MessageResponse,
    SessionResponse,
    SessionStartRequest,
    TableSetupRequest,
    TableSetupResponse,
)
from app.auth.service import AuthService
from app.core.config import get_settings
from app.core.context import TenantContext
from app.core.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
_settings = get_settings()


def _set_admin_cookie(response: Response, token: str) -> None:
    """HttpOnly + SameSite=Strict cookie; Secure in production. [SEC-12][SEC-04]"""
    response.set_cookie(
        key=ADMIN_COOKIE,
        value=token,
        max_age=_settings.jwt_expire_hours * 3600,
        httponly=True,
        secure=_settings.is_production,
        samesite="strict",
        path="/",
    )


@router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(
    body: AdminLoginRequest,
    response: Response,
    ip: str = Depends(client_ip),
    svc: AuthService = Depends(get_auth_service),
) -> AdminLoginResponse:
    store_id, token = svc.admin_login(body.store_code, body.admin_username, body.password, ip)
    _set_admin_cookie(response, token)
    return AdminLoginResponse(store_id=store_id)


@router.post("/admin/logout", response_model=MessageResponse)
def admin_logout(response: Response) -> MessageResponse:
    response.delete_cookie(key=ADMIN_COOKIE, path="/")
    return MessageResponse(message="logged out")


@router.post("/tables", response_model=TableSetupResponse)
def setup_table(
    body: TableSetupRequest,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
    ctx: TenantContext = Depends(require_admin),
) -> TableSetupResponse:
    table = svc.setup_table(ctx.store_id, body.table_no, body.table_password)
    result = TableSetupResponse(table_id=table.id, table_no=table.table_no)
    db.commit()
    return result


@router.post("/sessions", response_model=SessionResponse)
def start_session(
    body: SessionStartRequest,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
) -> SessionResponse:
    session = svc.start_session(body.store_code, body.table_no, body.table_password)
    result = SessionResponse(
        session_id=session.id,
        session_token=session.session_token,
        store_id=session.store_id,
        table_id=session.table_id,
    )
    db.commit()
    return result


@router.post("/sessions/close", response_model=MessageResponse)
def close_session(
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
    ctx: TenantContext = Depends(require_customer),
) -> MessageResponse:
    svc.close_session(ctx.session_id, ctx.store_id)
    db.commit()
    return MessageResponse(message="session closed")
