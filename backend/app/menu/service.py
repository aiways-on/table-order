"""MenuService — menu CRUD, grouping, reordering.  BR-M07~M20

Tenant isolation is enforced twice: MenuRepository force-filters by store_id
(first line) and this service operates only on rows the repository returns
(second line). [SEC-08][BR-M09]
"""
from __future__ import annotations

from app.core.errors import ValidationError
from app.menu.repository import MenuRepository
from app.menu.schemas import (
    MenuCategoryGroup,
    MenuCreate,
    MenuGroupedResponse,
    MenuOut,
    MenuUpdate,
)
from app.shared.models import Menu

_UNCATEGORIZED = "미분류"


class MenuService:
    def __init__(self, db):
        self.repo = MenuRepository(db)

    # --- read -----------------------------------------------------------

    def list_flat(self) -> list[MenuOut]:
        return [MenuOut.model_validate(m) for m in self.repo.list_ordered()]

    def list_grouped(self) -> MenuGroupedResponse:
        """Category-grouped view. BR-M19 — deterministic order.

        Rows arrive pre-sorted by (display_order, name); first appearance of a
        category therefore reflects its minimum display_order, so preserving
        insertion order yields the required group ordering.
        """
        groups: dict[str, list[MenuOut]] = {}
        for m in self.repo.list_ordered():
            key = m.category or _UNCATEGORIZED
            groups.setdefault(key, []).append(MenuOut.model_validate(m))
        return MenuGroupedResponse(
            groups=[MenuCategoryGroup(category=c, items=items) for c, items in groups.items()]
        )

    def get(self, menu_id: str) -> MenuOut:
        return MenuOut.model_validate(self.repo.get_or_404(menu_id))

    # --- write ----------------------------------------------------------

    def create(self, data: MenuCreate) -> MenuOut:
        order = data.display_order if data.display_order is not None else self.repo.max_display_order() + 1
        menu = Menu(
            name=data.name,
            price=data.price,
            category=data.category,
            description=data.description,
            image_url=data.image_url,
            display_order=order,
        )
        self.repo.add(menu)  # stamps store_id from context
        return MenuOut.model_validate(menu)

    def update(self, menu_id: str, data: MenuUpdate) -> MenuOut:
        menu = self.repo.get_or_404(menu_id)  # 404 for other tenants (IDOR) [SEC-08]
        menu.name = data.name
        menu.price = data.price
        menu.category = data.category
        menu.description = data.description
        menu.image_url = data.image_url
        if data.display_order is not None:
            menu.display_order = data.display_order
        self.repo.db.flush()
        return MenuOut.model_validate(menu)

    def delete(self, menu_id: str) -> None:
        self.repo.soft_delete(menu_id)  # get_or_404 inside → 404 if absent/other tenant/already gone

    def reorder(self, menu_ids: list[str]) -> int:
        """Atomically reassign display_order. BR-M14/M16.

        `menu_ids` must be an exact permutation of the store's non-deleted menu
        ids — otherwise reject wholesale (no partial application).
        """
        current = {m.id: m for m in self.repo.list_ordered()}
        requested = list(menu_ids)
        if len(requested) != len(set(requested)):
            raise ValidationError("duplicate menu ids")
        if set(requested) != set(current.keys()):
            raise ValidationError("menu_ids must be an exact permutation of current menus")
        for index, mid in enumerate(requested):
            current[mid].display_order = index
        self.repo.db.flush()
        return len(requested)
