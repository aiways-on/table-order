"""OrderService behaviour tests.  BR-O01~O19"""
from __future__ import annotations

import pytest

from app.auth import security
from app.core.context import Role, TenantContext, set_context
from app.core.errors import NotFoundError, ValidationError
from app.menu.schemas import MenuCreate
from app.menu.service import MenuService
from app.order.schemas import OrderCreate, OrderItemIn
from app.order.service import OrderService
from app.shared.models import (
    OrderStatus,
    SessionStatus,
    Store,
    Table,
    TableSession,
)


def _seed_store(db, store_code="CAFE01") -> Store:
    store = Store(
        store_code=store_code,
        name="Test Cafe",
        admin_username="owner",
        admin_password_hash=security.hash_password("password1"),
    )
    db.add(store)
    db.flush()
    return store


def _seed_session(db, store: Store) -> TableSession:
    table = Table(store_id=store.id, table_no=1, table_password_hash=security.hash_password("1234"))
    db.add(table)
    db.flush()
    session = TableSession(
        store_id=store.id,
        table_id=table.id,
        status=SessionStatus.ACTIVE,
        session_token=security.generate_session_token(),
    )
    db.add(session)
    db.flush()
    return session


def _customer_ctx(session: TableSession) -> TenantContext:
    ctx = TenantContext(
        store_id=session.store_id,
        role=Role.CUSTOMER,
        session_id=session.id,
        table_id=session.table_id,
        correlation_id="test",
    )
    set_context(ctx)
    return ctx


def _admin_ctx(store_id: str) -> TenantContext:
    ctx = TenantContext(store_id=store_id, role=Role.ADMIN, correlation_id="test")
    set_context(ctx)
    return ctx


def _menu(db, store: Store, name: str, price: int) -> str:
    _admin_ctx(store.id)
    return MenuService(db).create(MenuCreate(name=name, price=price, category="커피")).id


def test_create_snapshots_server_price_and_total(db_session):
    store = _seed_store(db_session)
    m1 = _menu(db_session, store, "아메리카노", 4000)
    m2 = _menu(db_session, store, "라떼", 4500)
    session = _seed_session(db_session, store)
    ctx = _customer_ctx(session)

    svc = OrderService(db_session)
    out = svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m1, qty=2), OrderItemIn(menu_id=m2, qty=1)]))

    assert out.order_no == 1
    assert out.total == 4000 * 2 + 4500  # BR-O02/O15
    assert {i.name for i in out.items} == {"아메리카노", "라떼"}
    assert out.status == OrderStatus.PENDING


def test_create_rejects_empty_cart():
    # BR-O03 — enforced by schema validation before any DB work.
    with pytest.raises(ValueError):
        OrderCreate(items=[])


def test_create_rejects_unavailable_menu(db_session):
    store = _seed_store(db_session)
    session = _seed_session(db_session, store)
    ctx = _customer_ctx(session)
    svc = OrderService(db_session)
    with pytest.raises(ValidationError):  # BR-O04
        svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id="does-not-exist", qty=1)]))


def test_order_no_is_sequential_and_not_reused_after_delete(db_session):
    store = _seed_store(db_session)
    m = _menu(db_session, store, "아메리카노", 4000)
    session = _seed_session(db_session, store)
    ctx = _customer_ctx(session)
    svc = OrderService(db_session)

    o1 = svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))
    o2 = svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))
    assert (o1.order_no, o2.order_no) == (1, 2)  # BR-O16

    _admin_ctx(store.id)
    svc.delete(o2.id)  # soft delete
    _customer_ctx(session)
    o3 = svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))
    assert o3.order_no == 3  # BR-O01 — deleted no. not reused


def test_update_status_free_transition(db_session):
    store = _seed_store(db_session)
    m = _menu(db_session, store, "아메리카노", 4000)
    session = _seed_session(db_session, store)
    ctx = _customer_ctx(session)
    svc = OrderService(db_session)
    order = svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))

    _admin_ctx(store.id)
    svc.update_status(order.id, OrderStatus.PREPARING)
    assert svc.get(order.id, _admin_ctx(store.id)).status == OrderStatus.PREPARING
    # BR-O10 — reverse correction allowed.
    svc.update_status(order.id, OrderStatus.PENDING)
    assert svc.get(order.id, _admin_ctx(store.id)).status == OrderStatus.PENDING


def test_close_session_moves_orders_to_history(db_session):
    store = _seed_store(db_session)
    m = _menu(db_session, store, "아메리카노", 4000)
    session = _seed_session(db_session, store)
    ctx = _customer_ctx(session)
    svc = OrderService(db_session)
    svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))
    svc.create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=3)]))

    _admin_ctx(store.id)
    svc.close_session(session.id)  # BR-O07

    # Active list now empty for that session.
    _customer_ctx(session)
    assert svc.list_session(ctx) == []
    # History preserves both orders.
    _admin_ctx(store.id)
    hist = svc.list_history()
    assert len(hist) == 2
    assert {h.total for h in hist} == {4000, 12000}  # BR-O08/O18
    assert all(h.session_closed_at is not None for h in hist)


def test_cross_tenant_get_is_404(db_session):
    store_a = _seed_store(db_session, "CAFE01")
    m = _menu(db_session, store_a, "아메리카노", 4000)
    session = _seed_session(db_session, store_a)
    ctx = _customer_ctx(session)
    order = OrderService(db_session).create(ctx, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))

    store_b = _seed_store(db_session, "CAFE02")
    _admin_ctx(store_b.id)
    with pytest.raises(NotFoundError):  # BR-O14 / SEC-08
        OrderService(db_session).get(order.id, TenantContext(store_id=store_b.id, role=Role.ADMIN))


def test_customer_cannot_read_other_session_order(db_session):
    store = _seed_store(db_session)
    m = _menu(db_session, store, "아메리카노", 4000)
    s1 = _seed_session(db_session, store)
    ctx1 = _customer_ctx(s1)
    order = OrderService(db_session).create(ctx1, OrderCreate(items=[OrderItemIn(menu_id=m, qty=1)]))

    # A different customer context (same store, different session id).
    other = TenantContext(
        store_id=store.id, role=Role.CUSTOMER, session_id="other-session", table_id="t2"
    )
    set_context(other)
    with pytest.raises(NotFoundError):  # BR-O14
        OrderService(db_session).get(order.id, other)
