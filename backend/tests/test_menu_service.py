"""MenuService behaviour tests.  BR-M07~M20"""
from __future__ import annotations

import pytest

from app.core.context import Role, TenantContext, set_context
from app.core.errors import NotFoundError, ValidationError
from app.menu.schemas import MenuCreate, MenuUpdate
from app.menu.service import MenuService


def _ctx(store_id: str) -> None:
    set_context(TenantContext(store_id=store_id, role=Role.ADMIN, correlation_id="test"))


def _create(svc: MenuService, name: str, price: int, category: str = "커피", order=None):
    return svc.create(MenuCreate(name=name, price=price, category=category, display_order=order))


def test_create_auto_display_order(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    m1 = _create(svc, "아메리카노", 4000)
    m2 = _create(svc, "라떼", 4500)
    # BR-M13: appends after the current max.
    assert m2.display_order == m1.display_order + 1


def test_update_replaces_fields(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    m = _create(svc, "아메리카노", 4000)
    out = svc.update(m.id, MenuUpdate(name="아메리카노(HOT)", price=4200, category="커피"))
    assert out.name == "아메리카노(HOT)"
    assert out.price == 4200


def test_soft_delete_excludes_from_list(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    m1 = _create(svc, "아메리카노", 4000)
    _create(svc, "라떼", 4500)
    svc.delete(m1.id)
    names = [i.name for g in svc.list_grouped().groups for i in g.items]
    assert "아메리카노" not in names
    assert "라떼" in names
    # BR-M12: deleting again -> 404.
    with pytest.raises(NotFoundError):
        svc.delete(m1.id)


def test_grouped_ordering(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    _create(svc, "아메리카노", 4000, category="커피")
    _create(svc, "녹차", 5000, category="티")
    _create(svc, "라떼", 4500, category="커피")
    resp = svc.list_grouped()
    # First group is the one containing the lowest display_order (커피, order 0).
    assert resp.groups[0].category == "커피"
    coffee = [i.name for i in resp.groups[0].items]
    assert coffee == ["아메리카노", "라떼"]  # display_order ascending


def test_reorder_permutation(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    a = _create(svc, "A", 1000)
    b = _create(svc, "B", 1000)
    c = _create(svc, "C", 1000)
    svc.reorder([c.id, a.id, b.id])
    order = [i.name for i in svc.list_flat()]
    assert order == ["C", "A", "B"]


def test_reorder_rejects_incomplete_set(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    a = _create(svc, "A", 1000)
    _create(svc, "B", 1000)
    with pytest.raises(ValidationError):
        svc.reorder([a.id])  # missing B -> reject wholesale


def test_reorder_rejects_foreign_id(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    a = _create(svc, "A", 1000)
    with pytest.raises(ValidationError):
        svc.reorder([a.id, "not-a-real-id"])


def test_cross_tenant_get_is_404(db_session):
    _ctx("store-a")
    svc = MenuService(db_session)
    m = _create(svc, "A", 1000)
    # Switch tenant: store-b must not see store-a's menu. BR-M07/M15
    _ctx("store-b")
    with pytest.raises(NotFoundError):
        svc.get(m.id)
    assert svc.list_flat() == []
