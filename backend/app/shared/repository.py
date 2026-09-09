"""Tenant-scoped repository base — first line of the dual-defense isolation.  [SEC-08][PBT-03]

Every query is force-filtered by the current context's store_id, and mutations
re-assert ownership before touching a row. Services re-check ownership too
(second line of defense) per BR-C04.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import require_store_id
from app.core.errors import ForbiddenError, NotFoundError

T = TypeVar("T")


class TenantScopedRepository(Generic[T]):
    """Base repository enforcing store_id scoping for a single model.

    The model MUST have a `store_id` column and (optionally) `deleted_at`.
    """

    model: type[T]

    def __init__(self, db: Session):
        self.db = db

    # --- internal helpers ------------------------------------------------

    def _base_query(self, include_deleted: bool = False):
        store_id = require_store_id()
        stmt = select(self.model).where(self.model.store_id == store_id)  # type: ignore[attr-defined]
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        return stmt

    # --- read ------------------------------------------------------------

    def get(self, entity_id: str, include_deleted: bool = False) -> T | None:
        stmt = self._base_query(include_deleted).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_404(self, entity_id: str) -> T:
        obj = self.get(entity_id)
        if obj is None:
            # Do not distinguish "not found" from "other tenant". [SEC-15][BR-C02]
            raise NotFoundError()
        return obj

    def list(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> list[T]:
        stmt = self._base_query(include_deleted).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    # --- write -----------------------------------------------------------

    def add(self, obj: T) -> T:
        """Stamp the tenant id from context and persist."""
        store_id = require_store_id()
        obj_store = getattr(obj, "store_id", None)
        if obj_store not in (None, store_id):
            # Refuse to create a row for a different tenant. [BR-C02]
            raise ForbiddenError()
        setattr(obj, "store_id", store_id)
        self.db.add(obj)
        self.db.flush()
        return obj

    def soft_delete(self, entity_id: str) -> None:
        """Soft delete (deleted_at) — model must support it.  [SEC-13]"""
        from datetime import datetime, timezone

        obj = self.get_or_404(entity_id)
        if not hasattr(obj, "deleted_at"):
            raise ForbiddenError("Soft delete unsupported for this model")
        setattr(obj, "deleted_at", datetime.now(timezone.utc))
        self.db.flush()
