"""Menu API tests via TestClient.  BR-M08 (read customer|admin, write admin)"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import security
from app.auth.service import _login_limiter
from app.core.context import reset_context
from app.core.database import Base, get_db
from app.main import create_app
from app.shared import models  # noqa: F401
from app.shared.models import Store


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

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


def _login_admin(client) -> None:
    r = client.post(
        "/api/auth/admin/login",
        json={"store_code": "CAFE01", "admin_username": "owner", "password": "password1"},
    )
    assert r.status_code == 200


def _start_customer_session(client) -> str:
    # Admin sets up a table, then a customer starts a session for the token.
    r = client.post("/api/auth/tables", json={"table_no": 1, "table_password": "1234"})
    assert r.status_code == 200
    r = client.post(
        "/api/auth/sessions",
        json={"store_code": "CAFE01", "table_no": 1, "table_password": "1234"},
    )
    assert r.status_code == 200
    return r.json()["session_token"]


def test_list_requires_auth(client):
    r = client.get("/api/menus")
    assert r.status_code == 401


def test_admin_create_and_list(client):
    _login_admin(client)
    r = client.post("/api/menus", json={"name": "아메리카노", "price": 4000, "category": "커피"})
    assert r.status_code == 201
    r = client.get("/api/menus")
    assert r.status_code == 200
    groups = r.json()["groups"]
    assert groups[0]["category"] == "커피"
    assert groups[0]["items"][0]["name"] == "아메리카노"


def test_create_rejects_negative_price(client):
    _login_admin(client)
    r = client.post("/api/menus", json={"name": "x", "price": -1, "category": "커피"})
    assert r.status_code == 422


def test_customer_can_read_but_not_write(client):
    _login_admin(client)
    client.post("/api/menus", json={"name": "라떼", "price": 4500, "category": "커피"})
    token = _start_customer_session(client)

    # Fresh client without the admin cookie, using only the session token.
    reader = TestClient(client.app)
    r = reader.get("/api/menus", headers={"X-Session-Token": token})
    assert r.status_code == 200
    assert r.json()["groups"][0]["items"][0]["name"] == "라떼"

    # Customer cannot create (no admin cookie -> 401).
    r = reader.post(
        "/api/menus",
        json={"name": "몰래", "price": 1, "category": "커피"},
        headers={"X-Session-Token": token},
    )
    assert r.status_code == 401


def test_reorder_flow(client):
    _login_admin(client)
    ids = []
    for name in ["A", "B", "C"]:
        r = client.post("/api/menus", json={"name": name, "price": 1000, "category": "커피"})
        ids.append(r.json()["id"])
    r = client.post("/api/menus/reorder", json={"menu_ids": [ids[2], ids[0], ids[1]]})
    assert r.status_code == 200
    assert r.json()["updated"] == 3
    r = client.get("/api/menus/flat")
    assert [m["name"] for m in r.json()] == ["C", "A", "B"]


def test_delete_removes_from_list(client):
    _login_admin(client)
    r = client.post("/api/menus", json={"name": "삭제대상", "price": 1000, "category": "커피"})
    menu_id = r.json()["id"]
    r = client.delete(f"/api/menus/{menu_id}")
    assert r.status_code == 204
    r = client.get("/api/menus/flat")
    assert all(m["id"] != menu_id for m in r.json())


def test_cross_tenant_get_404(client):
    _login_admin(client)
    r = client.get("/api/menus/nonexistent-id")
    assert r.status_code == 404
