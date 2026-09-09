"""Property-based tests for the tenant-isolation invariant.  [PBT-03][BR-C03]

Invariant: for any pair of distinct stores, a repository bound to store A can
never read, fetch, or delete a resource owned by store B.

Each generated example builds its own fresh in-memory DB (via `fresh_db`) so
Hypothesis examples stay fully isolated from one another.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.context import Role, TenantContext, reset_context, set_context
from app.core.database import Base
from app.core.errors import NotFoundError
from app.shared.models import Menu
from app.shared.repository import TenantScopedRepository


class MenuRepository(TenantScopedRepository[Menu]):
    model = Menu


@contextmanager
def fresh_db() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        reset_context()


def _use_store(store_id: str) -> None:
    set_context(TenantContext(store_id=store_id, role=Role.ADMIN, correlation_id="test"))


def _make_menu(name: str, price: int) -> Menu:
    return Menu(name=name, price=price)


menu_names = st.text(min_size=1, max_size=50)
prices = st.integers(min_value=0, max_value=1_000_000)


@settings(max_examples=50, deadline=None)
@given(name=menu_names, price=prices)
def test_cross_tenant_get_returns_none(name, price):
    with fresh_db() as db:
        store_a, store_b = str(uuid.uuid4()), str(uuid.uuid4())

        _use_store(store_a)
        created = MenuRepository(db).add(_make_menu(name, price))
        db.commit()
        menu_id = created.id

        _use_store(store_b)
        assert MenuRepository(db).get(menu_id) is None  # [BR-C02]


@settings(max_examples=50, deadline=None)
@given(name=menu_names, price=prices)
def test_cross_tenant_get_or_404_raises(name, price):
    with fresh_db() as db:
        store_a, store_b = str(uuid.uuid4()), str(uuid.uuid4())
        _use_store(store_a)
        created = MenuRepository(db).add(_make_menu(name, price))
        db.commit()

        _use_store(store_b)
        try:
            MenuRepository(db).get_or_404(created.id)
            raised = False
        except NotFoundError:
            raised = True
        assert raised, "cross-tenant access must be denied (generalized as not-found)"


@settings(max_examples=30, deadline=None)
@given(names=st.lists(menu_names, min_size=1, max_size=5))
def test_list_only_returns_own_tenant(names):
    with fresh_db() as db:
        store_a, store_b = str(uuid.uuid4()), str(uuid.uuid4())

        _use_store(store_a)
        for n in names:
            MenuRepository(db).add(_make_menu(n, 1000))
        db.commit()

        _use_store(store_b)
        assert MenuRepository(db).list() == []

        _use_store(store_a)
        assert len(MenuRepository(db).list(limit=500)) == len(names)
