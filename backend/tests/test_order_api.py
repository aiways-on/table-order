"""Order API tests via TestClient.  BR-O09/O13/O14 (auth, isolation, SSE smoke)"""
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


def _create_menu(client, name="아메리카노", price=4000) -> str:
    r = client.post("/api/menus", json={"name": name, "price": price, "category": "커피"})
    assert r.status_code == 201
    return r.json()["id"]


def _start_session(client) -> dict:
    r = client.post("/api/auth/tables", json={"table_no": 1, "table_password": "1234"})
    assert r.status_code == 200
    r = client.post(
        "/api/auth/sessions",
        json={"store_code": "CAFE01", "table_no": 1, "table_password": "1234"},
    )
    assert r.status_code == 200
    return r.json()  # {session_id, session_token, ...}


def _hdr(token: str) -> dict:
    return {"X-Session-Token": token}


# --- customer confirm / list -------------------------------------------

def test_customer_creates_and_lists_order(client):
    _login_admin(client)
    menu_id = _create_menu(client)
    session = _start_session(client)
    token = session["session_token"]

    r = client.post("/api/orders", headers=_hdr(token), json={"items": [{"menu_id": menu_id, "qty": 2}]})
    assert r.status_code == 201
    body = r.json()
    assert body["order_no"] == 1
    assert body["total"] == 8000

    r = client.get("/api/orders", headers=_hdr(token))
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_create_rejects_empty_and_unavailable(client):
    _login_admin(client)
    session = _start_session(client)
    token = session["session_token"]
    assert client.post("/api/orders", headers=_hdr(token), json={"items": []}).status_code == 422
    r = client.post("/api/orders", headers=_hdr(token), json={"items": [{"menu_id": "nope", "qty": 1}]})
    assert r.status_code == 422


def test_create_requires_session(client):
    _login_admin(client)
    menu_id = _create_menu(client)
    r = client.post("/api/orders", json={"items": [{"menu_id": menu_id, "qty": 1}]})
    assert r.status_code == 401


def test_client_sent_price_is_ignored(client):
    _login_admin(client)
    menu_id = _create_menu(client, price=4000)
    token = _start_session(client)["session_token"]
    r = client.post(
        "/api/orders",
        headers=_hdr(token),
        json={"items": [{"menu_id": menu_id, "qty": 1, "unit_price": 1}]},
    )
    assert r.status_code == 201
    assert r.json()["total"] == 4000  # BR-O17


# --- admin monitoring / status / delete --------------------------------

def test_admin_store_list_and_filter(client):
    _login_admin(client)
    menu_id = _create_menu(client)
    token = _start_session(client)["session_token"]
    client.post("/api/orders", headers=_hdr(token), json={"items": [{"menu_id": menu_id, "qty": 1}]})

    r = client.get("/api/orders/store")
    assert r.status_code == 200
    assert len(r.json()) == 1
    # Filter by a status with no matches.
    r = client.get("/api/orders/store", params={"status": "done"})
    assert r.status_code == 200 and r.json() == []


def test_admin_updates_status_and_deletes(client):
    _login_admin(client)
    menu_id = _create_menu(client)
    token = _start_session(client)["session_token"]
    order_id = client.post(
        "/api/orders", headers=_hdr(token), json={"items": [{"menu_id": menu_id, "qty": 1}]}
    ).json()["id"]

    r = client.patch(f"/api/orders/{order_id}/status", json={"status": "preparing"})
    assert r.status_code == 200 and r.json()["status"] == "preparing"
    # invalid status → 422
    assert client.patch(f"/api/orders/{order_id}/status", json={"status": "flying"}).status_code == 422

    assert client.delete(f"/api/orders/{order_id}").status_code == 204
    assert client.get("/api/orders", headers=_hdr(token)).json() == []


def test_status_change_requires_admin(client):
    _login_admin(client)
    menu_id = _create_menu(client)
    token = _start_session(client)["session_token"]
    order_id = client.post(
        "/api/orders", headers=_hdr(token), json={"items": [{"menu_id": menu_id, "qty": 1}]}
    ).json()["id"]
    client.post("/api/auth/admin/logout")  # drop admin cookie
    assert client.patch(f"/api/orders/{order_id}/status", json={"status": "done"}).status_code == 401


# --- session close → history --------------------------------------------

def test_close_session_moves_to_history(client):
    _login_admin(client)
    menu_id = _create_menu(client)
    session = _start_session(client)
    token = session["session_token"]
    client.post("/api/orders", headers=_hdr(token), json={"items": [{"menu_id": menu_id, "qty": 2}]})

    r = client.post(f"/api/sessions/{session['session_id']}/close")
    assert r.status_code == 204

    r = client.get("/api/history")
    assert r.status_code == 200
    hist = r.json()
    assert len(hist) == 1 and hist[0]["total"] == 8000
    # Session is now closed → the customer token no longer authenticates. BR-O05
    assert client.get("/api/orders", headers=_hdr(token)).status_code == 401


# --- SSE smoke ----------------------------------------------------------

def test_admin_sse_requires_auth(client):
    assert client.get("/api/orders/stream").status_code == 401


def test_customer_sse_requires_token(client):
    assert client.get("/api/orders/session/stream").status_code == 401


def test_admin_sse_connects(client):
    _login_admin(client)
    with client.stream("GET", "/api/orders/stream") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]


def test_customer_sse_connects(client):
    _login_admin(client)
    token = _start_session(client)["session_token"]
    with client.stream("GET", "/api/orders/session/stream", params={"token": token}) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
