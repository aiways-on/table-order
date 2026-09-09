"""Property-based tests for order invariants.  [PBT-03][PBT-06] BR-O15~O19

Each generated example builds a fresh in-memory DB (not the function-scoped
fixture) so Hypothesis re-runs are fully isolated.
"""
from __future__ import annotations

from contextlib import contextmanager

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import security
from app.core.context import Role, TenantContext, reset_context, set_context
from app.core.database import Base
from app.menu.schemas import MenuCreate
from app.menu.service import MenuService
from app.order.schemas import OrderCreate, OrderItemIn
from app.order.service import OrderService
from app.shared import models  # noqa: F401
from app.shared.models import SessionStatus, Store, Table, TableSession


@contextmanager
def fresh_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        reset_context()


def _setup(db, store_id="A"):
    """Seed a store + one active session; return (customer_ctx, admin_ctx)."""
    store = Store(
        id=store_id,
        store_code=f"CODE-{store_id}",
        name="Cafe",
        admin_username="owner",
        admin_password_hash=security.hash_password("password1"),
    )
    db.add(store)
    db.flush()
    table = Table(store_id=store_id, table_no=1, table_password_hash=security.hash_password("1234"))
    db.add(table)
    db.flush()
    session = TableSession(
        store_id=store_id,
        table_id=table.id,
        status=SessionStatus.ACTIVE,
        session_token=security.generate_session_token(),
    )
    db.add(session)
    db.flush()
    customer = TenantContext(
        store_id=store_id, role=Role.CUSTOMER, session_id=session.id, table_id=table.id
    )
    admin = TenantContext(store_id=store_id, role=Role.ADMIN)
    return customer, admin


def _make_menus(db, admin, prices):
    set_context(admin)
    svc = MenuService(db)
    return [svc.create(MenuCreate(name=f"m{i}", price=p, category="c")).id for i, p in enumerate(prices)]


_prices = st.integers(min_value=0, max_value=1_000_000)
_qtys = st.integers(min_value=1, max_value=20)
_lines = st.lists(st.tuples(_prices, _qtys), min_size=1, max_size=8)


@settings(max_examples=50, deadline=None)
@given(lines=_lines)
def test_total_equals_sum_of_lines(lines):
    """BR-O15: total == Σ(server unit_price × qty)."""
    with fresh_db() as db:
        customer, admin = _setup(db)
        prices = [p for p, _ in lines]
        menu_ids = _make_menus(db, admin, prices)
        set_context(customer)
        items = [OrderItemIn(menu_id=menu_ids[i], qty=q) for i, (_, q) in enumerate(lines)]
        out = OrderService(db).create(customer, OrderCreate(items=items))
        expected = sum(p * q for p, q in lines)
        assert out.total == expected
        assert all(it.unit_price == prices[i] for i, it in enumerate(out.items))


@settings(max_examples=40, deadline=None)
@given(n=st.integers(min_value=1, max_value=10), price=_prices)
def test_order_numbers_monotonic_unique(n, price):
    """BR-O16: consecutive orders get 1..n, strictly increasing and unique."""
    with fresh_db() as db:
        customer, admin = _setup(db)
        (mid,) = _make_menus(db, admin, [price])
        set_context(customer)
        svc = OrderService(db)
        nos = [svc.create(customer, OrderCreate(items=[OrderItemIn(menu_id=mid, qty=1)])).order_no
               for _ in range(n)]
        assert nos == list(range(1, n + 1))
        assert len(set(nos)) == n


@settings(max_examples=50, deadline=None)
@given(client_price=st.integers(), real_price=_prices, qty=_qtys)
def test_client_price_is_ignored(client_price, real_price, qty):
    """BR-O17: a spoofed client price never affects the stored snapshot/total."""
    with fresh_db() as db:
        customer, admin = _setup(db)
        (mid,) = _make_menus(db, admin, [real_price])
        set_context(customer)
        # Extra 'unit_price'/'price' keys are ignored by OrderItemIn (extra=ignore).
        item = OrderItemIn.model_validate({"menu_id": mid, "qty": qty, "unit_price": client_price, "price": client_price})
        out = OrderService(db).create(customer, OrderCreate(items=[item]))
        assert out.items[0].unit_price == real_price
        assert out.total == real_price * qty


@settings(max_examples=40, deadline=None)
@given(lines=_lines)
def test_history_round_trip_on_close(lines):
    """BR-O18: after close, history == active-before, and active becomes empty."""
    with fresh_db() as db:
        customer, admin = _setup(db)
        prices = [p for p, _ in lines]
        menu_ids = _make_menus(db, admin, prices)
        set_context(customer)
        svc = OrderService(db)
        before = []
        for i, (_, q) in enumerate(lines):
            o = svc.create(customer, OrderCreate(items=[OrderItemIn(menu_id=menu_ids[i], qty=q)]))
            before.append((o.order_no, o.total))

        set_context(admin)
        svc.close_session(customer.session_id)
        hist = svc.list_history()
        assert sorted((h.order_no, h.total) for h in hist) == sorted(before)
        set_context(customer)
        assert svc.list_session(customer) == []


@settings(max_examples=40, deadline=None)
@given(lines=_lines, seed=st.integers())
def test_delete_keeps_total_consistent(lines, seed):
    """BR-O19: after deleting a subset, table total == Σ remaining order totals."""
    import random

    with fresh_db() as db:
        customer, admin = _setup(db)
        prices = [p for p, _ in lines]
        menu_ids = _make_menus(db, admin, prices)
        set_context(customer)
        svc = OrderService(db)
        orders = [svc.create(customer, OrderCreate(items=[OrderItemIn(menu_id=menu_ids[i], qty=q)]))
                  for i, (_, q) in enumerate(lines)]

        set_context(admin)
        rng = random.Random(seed)
        to_delete = {o.id for o in orders if rng.random() < 0.5}
        for oid in to_delete:
            svc.delete(oid)

        remaining_expected = sum(o.total for o in orders if o.id not in to_delete)
        set_context(customer)
        remaining_actual = sum(o.total for o in svc.list_session(customer))
        assert remaining_actual == remaining_expected
