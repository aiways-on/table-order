"""Test fixtures: isolated in-memory SQLite DB per test.  [PBT-06]

Tests exercise cross-cutting logic (tenant isolation, soft delete, masking) that
is dialect-agnostic. PostgreSQL-specific behaviour (partial unique index) is
verified via the resiliency/integration tests in the Build & Test phase.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.context import TenantContext, Role, reset_context, set_context
from app.core.database import Base
from app.shared import models  # noqa: F401  (register mappers)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        reset_context()


@pytest.fixture
def as_store():
    """Return a helper that sets the tenant context to a given store_id."""

    def _set(store_id: str, role: Role = Role.ADMIN):
        set_context(TenantContext(store_id=store_id, role=role, correlation_id="test"))

    yield _set
    reset_context()
