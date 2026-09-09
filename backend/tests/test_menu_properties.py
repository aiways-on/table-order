"""Property-based tests for menu invariants.  [PBT-03][PBT-07] BR-M15~M18

Each generated example builds a fresh in-memory DB (not the function-scoped
fixture) so Hypothesis re-runs are fully isolated.
"""
from __future__ import annotations

from contextlib import contextmanager

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.context import Role, TenantContext, reset_context, set_context
from app.core.database import Base
from app.menu.schemas import MenuCreate
from app.menu.service import MenuService
from app.shared import models  # noqa: F401


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


def _use_store(store_id: str) -> None:
    set_context(TenantContext(store_id=store_id, role=Role.ADMIN, correlation_id="pbt"))


_names = st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=122), min_size=1, max_size=20)
_prices = st.integers(min_value=0, max_value=10_000_000)
_menus = st.lists(st.tuples(_names, _prices), min_size=1, max_size=6)


@settings(max_examples=40, deadline=None)
@given(a_menus=_menus, b_menus=_menus)
def test_tenant_isolation(a_menus, b_menus):
    """BR-M15: store A never sees store B's menus regardless of contents."""
    with fresh_db() as db:
        svc = MenuService(db)
        _use_store("A")
        a_ids = {svc.create(MenuCreate(name=n, price=p, category="c")).id for n, p in a_menus}
        _use_store("B")
        b_ids = {svc.create(MenuCreate(name=n, price=p, category="c")).id for n, p in b_menus}

        _use_store("A")
        seen = {m.id for m in svc.list_flat()}
        assert seen == a_ids
        assert seen.isdisjoint(b_ids)


@settings(max_examples=40, deadline=None)
@given(menus=_menus, seed=st.integers())
def test_reorder_is_permutation(menus, seed):
    """BR-M16: reorder applies the requested order and preserves the id set."""
    with fresh_db() as db:
        svc = MenuService(db)
        _use_store("A")
        ids = [svc.create(MenuCreate(name=n, price=p, category="c")).id for n, p in menus]
        # Deterministic shuffle from the seed.
        import random

        order = ids[:]
        random.Random(seed).shuffle(order)
        svc.reorder(order)
        after = [m.id for m in svc.list_flat()]
        assert after == order
        assert set(after) == set(ids)


@settings(max_examples=40, deadline=None)
@given(menus=st.lists(st.tuples(_names, _prices), min_size=2, max_size=6), idx=st.integers())
def test_soft_delete_monotonic(menus, idx):
    """BR-M17: deleting one menu drops exactly it; others are unchanged."""
    with fresh_db() as db:
        svc = MenuService(db)
        _use_store("A")
        ids = [svc.create(MenuCreate(name=n, price=p, category="c")).id for n, p in menus]
        target = ids[idx % len(ids)]
        before = {m.id for m in svc.list_flat()}
        svc.delete(target)
        after = {m.id for m in svc.list_flat()}
        assert after == before - {target}
        assert len(after) == len(before) - 1


@settings(max_examples=40, deadline=None)
@given(name=_names, price=_prices)
def test_price_round_trip(name, price):
    """BR-M18: a valid price survives create -> fetch unchanged."""
    with fresh_db() as db:
        svc = MenuService(db)
        _use_store("A")
        created = svc.create(MenuCreate(name=name, price=price, category="c"))
        fetched = svc.get(created.id)
        assert fetched.price == price
