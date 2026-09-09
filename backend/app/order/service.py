"""OrderService — order lifecycle, session close→history, isolation.  BR-O01~O19

Tenant isolation is enforced twice: OrderRepository force-filters by store_id
(first line) and this service operates only on rows the repository returns +
re-checks customer session ownership (second line). [SEC-08][BR-O14]

Atomicity: create and close_session mutate within a single request transaction;
the router commits, and SSE events are published only after commit. [BR-O06]
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.core.context import Role, TenantContext
from app.core.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from app.menu.service import MenuService
from app.order.repository import OrderRepository
from app.order.schemas import HistoryOut, OrderCreate, OrderOut
from app.shared.models import Order, OrderHistory, OrderStatus, SessionStatus

_MAX_ORDER_NO_RETRIES = 3


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _status_value(status) -> str:
    return status.value if isinstance(status, OrderStatus) else str(status)


class OrderService:
    def __init__(self, db):
        self.db = db
        self.repo = OrderRepository(db)
        self.menu = MenuService(db)

    # --- customer: create / list ----------------------------------------

    def create(self, ctx: TenantContext, data: OrderCreate) -> OrderOut:
        """Confirm an order for the active session. BR-O01~O06, O15~O17

        Prices/names come from the server menu (client input ignored). order_no
        is allocated per session; a unique-constraint race is retried, then 409.
        """
        if not ctx.session_id or not ctx.table_id:
            # require_customer guarantees these; fail closed otherwise. [SEC-15]
            raise UnauthorizedError("Session required")

        items: list[dict] = []
        total = 0
        for line in data.items:
            menu = self._resolve_menu(line.menu_id)  # BR-O04 (own, non-deleted)
            items.append(
                {"menu_id": menu.id, "name": menu.name, "unit_price": menu.price, "qty": line.qty}
            )
            total += menu.price * line.qty  # BR-O02/O15

        for _ in range(_MAX_ORDER_NO_RETRIES):
            order_no = self.repo.max_order_no(ctx.session_id) + 1  # BR-O01
            order = Order(
                table_id=ctx.table_id,
                session_id=ctx.session_id,
                order_no=order_no,
                items=items,
                total=total,
                status=OrderStatus.PENDING,
            )
            try:
                self.repo.add(order)  # stamps store_id + flush
                return OrderOut.model_validate(order)
            except IntegrityError:
                self.db.rollback()  # concurrent allocation took this order_no; retry
        raise ConflictError("Could not allocate order number, please retry")  # BR-O01

    def list_session(self, ctx: TenantContext, limit: int = 100, offset: int = 0) -> list[OrderOut]:
        """Current session's non-deleted orders (customer). BR-O13"""
        if not ctx.session_id:
            raise UnauthorizedError("Session required")
        rows = self.repo.session_orders(ctx.session_id, limit=limit, offset=offset)
        return [OrderOut.model_validate(o) for o in rows]

    # --- shared: detail --------------------------------------------------

    def get(self, order_id: str, ctx: TenantContext) -> OrderOut:
        """Order detail. Customer may only read orders in their own session. BR-O14"""
        order = self.repo.get_or_404(order_id)  # store-scoped (IDOR → 404)
        if ctx.role == Role.CUSTOMER and order.session_id != ctx.session_id:
            raise NotFoundError()  # no existence leak across sessions [SEC-15]
        return OrderOut.model_validate(order)

    # --- admin: monitoring / status / delete -----------------------------

    def list_store(
        self, table_id: str | None = None, status: OrderStatus | None = None
    ) -> list[OrderOut]:
        """Store-wide monitoring list with optional filters (admin). BR-O13"""
        rows = self.repo.store_orders(table_id=table_id, status=status)
        return [OrderOut.model_validate(o) for o in rows]

    def update_status(self, order_id: str, status: OrderStatus) -> OrderOut:
        """Set order status (admin, free transitions among enum values). BR-O10"""
        order = self.repo.get_or_404(order_id)
        order.status = status
        self.db.flush()
        return OrderOut.model_validate(order)

    def delete(self, order_id: str) -> OrderOut:
        """Soft-delete an order (admin); returns the pre-delete snapshot. BR-O11/O19"""
        order = self.repo.get_or_404(order_id)
        out = OrderOut.model_validate(order)
        order.deleted_at = _utcnow()
        self.db.flush()
        return out

    # --- admin: session close → history ----------------------------------

    def close_session(self, session_id: str) -> tuple[str, str]:
        """Close a session: copy active orders to history, soft-delete originals.

        Returns (session_id, table_id). BR-O07/O08/O09/O18
        """
        session = self.repo.get_session(session_id)
        if session is None:
            raise NotFoundError()  # absent or other tenant [SEC-08]

        now = _utcnow()
        for order in self.repo.session_orders(session_id):
            self.repo.add_history(
                OrderHistory(
                    store_id=order.store_id,
                    table_id=order.table_id,
                    session_id=order.session_id,
                    original_order_id=order.id,
                    order_no=order.order_no,
                    items=order.items,
                    total=order.total,
                    status=_status_value(order.status),
                    created_at=order.created_at,
                    session_closed_at=now,
                )
            )
            order.deleted_at = now  # soft-delete original [BR-O07]

        session.status = SessionStatus.CLOSED
        session.closed_at = now
        self.db.flush()
        return session.id, session.table_id

    def list_history(
        self, table_id: str | None = None, date_from=None, date_to=None
    ) -> list[HistoryOut]:
        """Past orders from closed sessions (admin). BR-O08/O13"""
        rows = self.repo.list_history(table_id=table_id, date_from=date_from, date_to=date_to)
        return [HistoryOut.model_validate(h) for h in rows]

    # --- helpers ---------------------------------------------------------

    def _resolve_menu(self, menu_id: str):
        """Server-side menu lookup; unavailable/other-tenant item → 422. BR-O04"""
        try:
            return self.menu.get(menu_id)
        except NotFoundError:
            raise ValidationError("Order contains an unavailable menu item")
