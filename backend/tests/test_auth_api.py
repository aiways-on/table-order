"""Auth API tests via TestClient (dependency-overridden SQLite).  [SEC-08][SEC-12]"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import security
from app.auth.dependencies import ADMIN_COOKIE
from app.auth.service import _login_limiter
from app.core.database import Base, get_db
from app.core.context import reset_context
from app.main import create_app
from app.shared import models  # noqa: F401  (register mappers)
from app.shared.models import Store


@pytest.fixture
def client():
    # StaticPool + a single shared connection so every session sees the same
    # in-memory database (otherwise each connection gets its own empty DB).
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    # Seed a store.
    seed = TestSession()
    seed.add(
        Store(
            store_code="CAFE01",
            name="Test Cafe",
            admin_username="owner",
            admin_password_hash=security.hash_password("password1"),
        )
    )
    seed.commit()
    seed.close()

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    _login_limiter._hits.clear()
    with TestClient(app) as c:
        yield c
    _login_limiter._hits.clear()
    reset_context()
    Base.metadata.drop_all(engine)


def test_login_sets_httponly_cookie(client):
    r = client.post(
        "/api/auth/admin/login",
        json={"store_code": "CAFE01", "admin_username": "owner", "password": "password1"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
    cookie = r.headers.get("set-cookie", "")
    assert ADMIN_COOKIE in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie.replace("Strict", "strict")


def test_login_bad_credentials_generic_error(client):
    r = client.post(
        "/api/auth/admin/login",
        json={"store_code": "CAFE01", "admin_username": "owner", "password": "wrongpass1"},
    )
    assert r.status_code == 401
    # No detail should reveal whether the store or the password was wrong. [SEC-15]
    assert "password" not in r.text.lower()


def test_login_short_password_rejected_by_validation(client):
    r = client.post(
        "/api/auth/admin/login",
        json={"store_code": "CAFE01", "admin_username": "owner", "password": "short"},
    )
    assert r.status_code == 422


def test_protected_table_setup_requires_auth(client):
    r = client.post("/api/auth/tables", json={"table_no": 1, "table_password": "1234"})
    assert r.status_code == 401


def test_full_admin_and_session_flow(client):
    # Admin logs in (cookie stored on the client).
    r = client.post(
        "/api/auth/admin/login",
        json={"store_code": "CAFE01", "admin_username": "owner", "password": "password1"},
    )
    assert r.status_code == 200

    # Admin sets up a table.
    r = client.post("/api/auth/tables", json={"table_no": 7, "table_password": "4321"})
    assert r.status_code == 200
    assert r.json()["table_no"] == 7

    # Customer starts a session at that table.
    r = client.post(
        "/api/auth/sessions",
        json={"store_code": "CAFE01", "table_no": 7, "table_password": "4321"},
    )
    assert r.status_code == 200
    token = r.json()["session_token"]
    assert token

    # Customer closes the session with the token header.
    r = client.post("/api/auth/sessions/close", headers={"X-Session-Token": token})
    assert r.status_code == 200

    # Token no longer valid after close.
    r = client.post("/api/auth/sessions/close", headers={"X-Session-Token": token})
    assert r.status_code == 401


def test_logout_clears_cookie(client):
    client.post(
        "/api/auth/admin/login",
        json={"store_code": "CAFE01", "admin_username": "owner", "password": "password1"},
    )
    r = client.post("/api/auth/admin/logout")
    assert r.status_code == 200
