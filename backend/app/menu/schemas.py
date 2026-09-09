"""Menu request/response schemas (Pydantic validation).  [SEC-05] BR-M01~M06"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

_URL_PREFIXES = ("http://", "https://")


class _MenuFields(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=0)  # KRW; matches ck_menu_price_nonneg
    category: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("name", "category")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("image_url")
    @classmethod
    def _url_scheme(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.startswith(_URL_PREFIXES):
            raise ValueError("image_url must start with http:// or https://")
        return v


class MenuCreate(_MenuFields):
    display_order: int | None = Field(default=None, ge=0)


class MenuUpdate(_MenuFields):
    """Full replacement of editable fields (same rules as create). BR-M06"""

    display_order: int | None = Field(default=None, ge=0)


class MenuOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price: int
    category: str | None
    description: str | None
    image_url: str | None
    display_order: int


class MenuCategoryGroup(BaseModel):
    category: str
    items: list[MenuOut]


class MenuGroupedResponse(BaseModel):
    groups: list[MenuCategoryGroup]


class ReorderRequest(BaseModel):
    """Desired display order as an exact permutation of the store's menu ids. BR-M14"""

    menu_ids: list[str] = Field(min_length=1)


class ReorderResponse(BaseModel):
    updated: int
