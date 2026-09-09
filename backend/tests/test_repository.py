"""Repository behaviour: stamping, soft delete, ownership on create.  [SEC-08][SEC-13]"""
from __future__ import annotations

import uuid

import pytest

from app.core.errors import ForbiddenError, NotFoundError
from app.shared.models import Menu
from app.shared.repository import TenantScopedRepository


class MenuRepository(TenantScopedRepository[Menu]):
    model = Menu


def test_add_stamps_context_store_id(db_session, as_store):
    store = str(uuid.uuid4())
    as_store(store)
    repo = MenuRepository(db_session)
    m = repo.add(Menu(name="Latte", price=4500))
    db_session.commit()
    assert m.store_id == store


def test_add_rejects_foreign_store_id(db_session, as_store):
    store = str(uuid.uuid4())
    other = str(uuid.uuid4())
    as_store(store)
    repo = MenuRepository(db_session)
    with pytest.raises(ForbiddenError):
        repo.add(Menu(store_id=other, name="X", price=1))


def test_soft_delete_excludes_from_queries(db_session, as_store):
    store = str(uuid.uuid4())
    as_store(store)
    repo = MenuRepository(db_session)
    m = repo.add(Menu(name="Tea", price=3000))
    db_session.commit()

    repo.soft_delete(m.id)
    db_session.commit()

    assert repo.get(m.id) is None          # excluded by default [BR-C13]
    assert repo.list() == []
    # still retrievable when explicitly including deleted
    assert repo.get(m.id, include_deleted=True) is not None


def test_get_or_404_when_missing(db_session, as_store):
    as_store(str(uuid.uuid4()))
    repo = MenuRepository(db_session)
    with pytest.raises(NotFoundError):
        repo.get_or_404(str(uuid.uuid4()))
