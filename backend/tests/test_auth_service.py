"""AuthService behaviour tests.  BR-A01..A17, A19"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.auth import security
from app.auth.service import AuthService, _login_limiter
from app.core.config import get_settings
from app.core.errors import NotFoundError, RateLimitError, UnauthorizedError
from app.shared.models import SessionStatus, Store, Table, TableSession

_settings = get_settings()


@pytest.fixture(autouse=True)
def _clear_rate_limiter():
    _login_limiter._hits.clear()
    yield
    _login_limiter._hits.clear()


def _make_store(db, store_code="CAFE01", username="owner", password="password1") -> Store:
    store = Store(
        store_code=store_code,
        name="Test Cafe",
        admin_username=username,
        admin_password_hash=security.hash_password(password),
    )
    db.add(store)
    db.flush()
    return store


# --- admin_login --------------------------------------------------------

def test_admin_login_success(db_session):
    _make_store(db_session)
    svc = AuthService(db_session)
    store_id, token = svc.admin_login("CAFE01", "owner", "password1", "1.2.3.4")
    assert store_id
    claims = security.decode_admin_token(token)
    assert claims["sub"] == store_id


def test_admin_login_wrong_password(db_session):
    _make_store(db_session)
    svc = AuthService(db_session)
    with pytest.raises(UnauthorizedError):
        svc.admin_login("CAFE01", "owner", "wrong-password", "1.2.3.4")


def test_admin_login_unknown_store(db_session):
    svc = AuthService(db_session)
    with pytest.raises(UnauthorizedError):
        svc.admin_login("NOPE", "owner", "password1", "1.2.3.4")


def test_admin_login_rate_limited(db_session):
    _make_store(db_session)
    svc = AuthService(db_session)
    # Exhaust the window with failed attempts. [SEC-11]
    for _ in range(_settings.login_rate_limit):
        with pytest.raises(UnauthorizedError):
            svc.admin_login("CAFE01", "owner", "wrong", "9.9.9.9")
    with pytest.raises(RateLimitError):
        svc.admin_login("CAFE01", "owner", "wrong", "9.9.9.9")


def test_admin_login_success_resets_limit(db_session):
    _make_store(db_session)
    svc = AuthService(db_session)
    for _ in range(_settings.login_rate_limit - 1):
        with pytest.raises(UnauthorizedError):
            svc.admin_login("CAFE01", "owner", "wrong", "5.5.5.5")
    # A correct login clears the counter so the next attempt is not throttled.
    svc.admin_login("CAFE01", "owner", "password1", "5.5.5.5")
    store_id, _ = svc.admin_login("CAFE01", "owner", "password1", "5.5.5.5")
    assert store_id


# --- setup_table --------------------------------------------------------

def test_setup_table_creates_then_updates(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    t1 = svc.setup_table(store.id, 5, "1234")
    assert t1.table_no == 5
    assert security.verify_password("1234", t1.table_password_hash)
    # Re-setup updates the password in place (same row).
    t2 = svc.setup_table(store.id, 5, "5678")
    assert t2.id == t1.id
    assert security.verify_password("5678", t2.table_password_hash)


# --- start_session ------------------------------------------------------

def test_start_session_creates_and_reuses(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    svc.setup_table(store.id, 3, "9999")
    s1 = svc.start_session("CAFE01", 3, "9999")
    assert s1.status == SessionStatus.ACTIVE
    # Auto-login: a second start returns the same active session. BR-A14
    s2 = svc.start_session("CAFE01", 3, "9999")
    assert s2.id == s1.id


def test_start_session_wrong_password(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    svc.setup_table(store.id, 3, "9999")
    with pytest.raises(UnauthorizedError):
        svc.start_session("CAFE01", 3, "0000")


def test_start_session_unknown_table(db_session):
    _make_store(db_session)
    svc = AuthService(db_session)
    with pytest.raises(UnauthorizedError):
        svc.start_session("CAFE01", 99, "9999")


# --- verify_session / expiry (BR-A19) -----------------------------------

def test_verify_session_ok(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    svc.setup_table(store.id, 1, "1111")
    s = svc.start_session("CAFE01", 1, "1111")
    assert svc.verify_session(s.session_token).id == s.id


def test_verify_session_expired_rejected(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    svc.setup_table(store.id, 1, "1111")
    s = svc.start_session("CAFE01", 1, "1111")
    # Backdate beyond the expiry window. BR-A19
    s.started_at = datetime.now(timezone.utc) - timedelta(hours=_settings.jwt_expire_hours + 1)
    db_session.flush()
    with pytest.raises(UnauthorizedError):
        svc.verify_session(s.session_token)


def test_verify_session_closed_rejected(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    svc.setup_table(store.id, 1, "1111")
    s = svc.start_session("CAFE01", 1, "1111")
    svc.close_session(s.id, store.id)
    with pytest.raises(UnauthorizedError):
        svc.verify_session(s.session_token)


# --- close_session ownership (BR-A17) -----------------------------------

def test_close_session_cross_store_forbidden(db_session):
    store = _make_store(db_session)
    svc = AuthService(db_session)
    svc.setup_table(store.id, 1, "1111")
    s = svc.start_session("CAFE01", 1, "1111")
    # Another store must not be able to close this session (no leak → NotFound).
    with pytest.raises(NotFoundError):
        svc.close_session(s.id, "some-other-store-id")
    assert svc.verify_session(s.session_token).id == s.id
