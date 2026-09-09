"""Menu repository — tenant-scoped access to the Menu model.  [SEC-08]"""
from __future__ import annotations

from app.shared.models import Menu
from app.shared.repository import TenantScopedRepository


class MenuRepository(TenantScopedRepository[Menu]):
    model = Menu

    def list_ordered(self) -> list[Menu]:
        """All non-deleted menus for the current store, display_order then name."""
        stmt = self._base_query().order_by(Menu.display_order.asc(), Menu.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def max_display_order(self) -> int:
        """Highest display_order in the store (-1 if none) — for append-on-create. BR-M13"""
        rows = self._base_query().with_only_columns(Menu.display_order)
        values = [r for r in self.db.execute(rows).scalars().all()]
        return max(values) if values else -1
