"""Order repository — tenant-scoped access to Order / TableSession / OrderHistory.

First line of the dual-defense isolation: every query is force-filtered by the
current context's store_id (via TenantScopedRepository). Services re-check
ownership as the second line. [SEC-08][BR-O14]

order_no allocation deliberately counts ALL rows (including soft-deleted) so a
deleted order_no is never reused — the (session_id, order_no) UniqueConstraint
still occupies deleted rows. [BR-O01][BR-O16]
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.core.context import require_store_id
from app.shared.models import Order, OrderHistory, OrderStatus, TableSession
from app.shared.repository import TenantScopedRepository


class OrderRepository(TenantScopedRepository[Order]):
    model = Order

    # --- orders ----------------------------------------------------------

    def max_order_no(self, session_id: str) -> int:
        """Highest order_no in the session incl. soft-deleted (0 if none). BR-O01"""
        store_id = require_store_id()
        stmt = select(func.max(Order.order_no)).where(
            Order.store_id == store_id, Order.session_id == session_id
        )
        return self.db.execute(stmt).scalar() or 0

    def session_orders(
        self, session_id: str, limit: int | None = None, offset: int = 0
    ) -> list[Order]:
        """Non-deleted orders for a session, oldest first. BR-O13"""
        stmt = (
            self._base_query()
            .where(Order.session_id == session_id)
            .order_by(Order.created_at.asc(), Order.order_no.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def store_orders(
        self, table_id: str | None = None, status: OrderStatus | None = None
    ) -> list[Order]:
        """Store-wide non-deleted orders, newest first, optional filters. BR-O13"""
        stmt = self._base_query()
        if table_id:
            stmt = stmt.where(Order.table_id == table_id)
        if status is not None:
            stmt = stmt.where(Order.status == status)
        stmt = stmt.order_by(Order.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    # --- sessions --------------------------------------------------------

    def get_session(self, session_id: str) -> TableSession | None:
        """Session within the current store (ownership scoped). BR-O09"""
        store_id = require_store_id()
        stmt = select(TableSession).where(
            TableSession.id == session_id, TableSession.store_id == store_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # --- history ---------------------------------------------------------

    def add_history(self, history: OrderHistory) -> None:
        self.db.add(history)

    def list_history(
        self,
        table_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[OrderHistory]:
        """Past (closed-session) orders for the store, most recent first. BR-O08/O13"""
        store_id = require_store_id()
        stmt = select(OrderHistory).where(OrderHistory.store_id == store_id)
        if table_id:
            stmt = stmt.where(OrderHistory.table_id == table_id)
        if date_from:
            stmt = stmt.where(OrderHistory.created_at >= date_from)
        if date_to:
            stmt = stmt.where(OrderHistory.created_at <= date_to)
        stmt = stmt.order_by(OrderHistory.moved_at.desc(), OrderHistory.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())
