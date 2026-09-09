"""Order request/response schemas (Pydantic validation).  [SEC-05] BR-O02/O03

Note: order creation intentionally accepts only (menu_id, qty). Price and name
are NEVER taken from the client — the server re-fetches them from the menu and
builds the item snapshot itself. [SEC-05][BR-O17]
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.models import OrderStatus


class OrderItemIn(BaseModel):
    """A single requested line. Extra fields (e.g. a spoofed price) are ignored."""

    model_config = ConfigDict(extra="ignore")

    menu_id: str = Field(min_length=1)
    qty: int = Field(ge=1)  # BR-O03


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1)  # BR-O03 (reject empty cart)


class OrderItemOut(BaseModel):
    menu_id: str
    name: str
    unit_price: int
    qty: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_no: int
    table_id: str
    session_id: str
    items: list[OrderItemOut]
    total: int
    status: OrderStatus
    created_at: datetime


class StatusUpdate(BaseModel):
    status: OrderStatus  # BR-O10 — enum only (pending|preparing|done)


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_order_id: str
    order_no: int
    table_id: str
    session_id: str
    items: list[OrderItemOut]
    total: int
    status: str
    created_at: datetime
    session_closed_at: datetime | None = None
