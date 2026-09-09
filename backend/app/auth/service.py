"""AuthService — admin login, session lifecycle.  BR-A01~A17

Login and session-start run *before* a tenant context exists, so they query
Store/Table directly (not via TenantScopedRepository). Once authenticated they
establish the TenantContext for the rest of the request.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import security
from app.core.config import get_settings
from app.core.errors import ForbiddenError, NotFoundError, RateLimitError, UnauthorizedError
from app.core.notifier import get_notifier
from app.core.ratelimit import RateLimiter
from app.shared.models import SessionStatus, Store, Table, TableSession

_settings = get_settings()

# Login attempt limiter (account+IP key). [SEC-12]
_login_limiter = RateLimiter(_settings.login_rate_limit, _settings.login_rate_window_seconds)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """Normalize possibly-naive DB datetimes to UTC-aware for comparison."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.notifier = get_notifier()

    # --- Admin login [US-AUTH-01/02/03] ---------------------------------

    def admin_login(self, store_code: str, username: str, password: str, client_ip: str) -> tuple[str, str]:
        """Return (store_id, jwt_token) or raise. Generalized errors on failure. [SEC-15]"""
        rate_key = f"login:{store_code}:{username}:{client_ip}"
        if not _login_limiter.allow(rate_key):
            self.notifier.notify_security_event("login_rate_limited", store_code=store_code, ip=client_ip)
            raise RateLimitError()

        store = self.db.execute(select(Store).where(Store.store_code == store_code)).scalar_one_or_none()
        # Constant-ish path: verify even when store missing to avoid trivial enumeration.
        valid = (
            store is not None
            and store.admin_username == username
            and security.verify_password(password, store.admin_password_hash)
        )
        if not valid:
            self.notifier.notify_security_event("login_failed", store_code=store_code, ip=client_ip)
            raise UnauthorizedError("Invalid credentials")

        _login_limiter.reset(rate_key)
        token = security.create_admin_token(store.id)
        return store.id, token

    # --- Table setup (admin) [US-AUTH-04] -------------------------------

    def setup_table(self, store_id: str, table_no: int, table_password: str) -> Table:
        """Create or update a table's access password within the admin's store. [SEC-08]"""
        table = self.db.execute(
            select(Table).where(Table.store_id == store_id, Table.table_no == table_no)
        ).scalar_one_or_none()
        pw_hash = security.hash_password(table_password)
        if table is None:
            table = Table(store_id=store_id, table_no=table_no, table_password_hash=pw_hash)
            self.db.add(table)
        else:
            table.table_password_hash = pw_hash
        self.db.flush()
        return table

    # --- Session start / auto-login [US-AUTH-05] ------------------------

    def start_session(self, store_code: str, table_no: int, table_password: str) -> TableSession:
        """Verify table password; reuse the active session or create one. BR-A14"""
        store = self.db.execute(select(Store).where(Store.store_code == store_code)).scalar_one_or_none()
        table = None
        if store is not None:
            table = self.db.execute(
                select(Table).where(Table.store_id == store.id, Table.table_no == table_no)
            ).scalar_one_or_none()
        if table is None or not security.verify_password(table_password, table.table_password_hash):
            self.notifier.notify_security_event("table_auth_failed", store_code=store_code, table_no=table_no)
            raise UnauthorizedError("Invalid table credentials")

        existing = self.db.execute(
            select(TableSession).where(
                TableSession.table_id == table.id,
                TableSession.status == SessionStatus.ACTIVE,
            )
        ).scalar_one_or_none()
        if existing is not None and not self._is_expired(existing):
            return existing
        if existing is not None:
            # Expired active session -> close it before opening a new one.
            existing.status = SessionStatus.CLOSED
            existing.closed_at = _utcnow()
            self.db.flush()

        session = TableSession(
            store_id=store.id,
            table_id=table.id,
            status=SessionStatus.ACTIVE,
            session_token=security.generate_session_token(),
            started_at=_utcnow(),
        )
        self.db.add(session)
        self.db.flush()
        return session

    def verify_session(self, session_token: str) -> TableSession:
        """Resolve an active, non-expired session from its token. BR-A15/A19"""
        session = self.db.execute(
            select(TableSession).where(TableSession.session_token == session_token)
        ).scalar_one_or_none()
        if session is None or session.status != SessionStatus.ACTIVE or self._is_expired(session):
            raise UnauthorizedError("Invalid or expired session")
        return session

    def close_session(self, session_id: str, store_id: str) -> None:
        """Close a session within the caller's store (ownership re-check). BR-A17"""
        session = self.db.get(TableSession, session_id)
        if session is None or session.store_id != store_id:
            raise NotFoundError()
        session.status = SessionStatus.CLOSED
        session.closed_at = _utcnow()
        self.db.flush()

    # --- helpers ---------------------------------------------------------

    def _is_expired(self, session: TableSession) -> bool:
        expiry = _aware(session.started_at) + timedelta(hours=_settings.jwt_expire_hours)
        return _utcnow() > expiry
