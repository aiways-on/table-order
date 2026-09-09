"""SSE topic + payload helpers for order/session events.  [NFR-P2] BR-O12

Two topics per store:
- store:{store_id}      → admin monitoring grid (all tables)
- session:{session_id}  → a single customer's own session

Every mutating action publishes to BOTH the store topic and the affected
session topic so admin and customer screens update together. Events are
published only AFTER the DB commit succeeds. [BR-O06][BR-O12]
"""
from __future__ import annotations

from typing import Any

from app.order.schemas import OrderOut
from app.shared.models import OrderStatus


def store_topic(store_id: str) -> str:
    return f"store:{store_id}"


def session_topic(session_id: str) -> str:
    return f"session:{session_id}"


def _status(value: Any) -> str:
    return value.value if isinstance(value, OrderStatus) else str(value)


def order_created_event(order: OrderOut) -> dict[str, Any]:
    return {
        "type": "order_created",
        "order_id": order.id,
        "order_no": order.order_no,
        "table_id": order.table_id,
        "session_id": order.session_id,
        "total": order.total,
        "status": _status(order.status),
    }


def order_status_event(order: OrderOut) -> dict[str, Any]:
    return {
        "type": "order_status",
        "order_id": order.id,
        "table_id": order.table_id,
        "session_id": order.session_id,
        "status": _status(order.status),
    }


def order_deleted_event(order: OrderOut) -> dict[str, Any]:
    return {
        "type": "order_deleted",
        "order_id": order.id,
        "table_id": order.table_id,
        "session_id": order.session_id,
    }


def session_closed_event(session_id: str, table_id: str) -> dict[str, Any]:
    return {
        "type": "session_closed",
        "session_id": session_id,
        "table_id": table_id,
    }
