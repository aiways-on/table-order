"""Shared SQLAlchemy domain models.  [BR-C10][BR-C11][SEC-08][SEC-13]

Conventions (from functional-design/domain-entities.md):
- UUID(v4) string primary keys                          [BR-C10]
- All timestamps stored as timezone-aware UTC           [BR-C11]
- Every tenant entity carries store_id + composite index [SEC-08]
- Soft delete via deleted_at on Menu / Order            [SEC-13]
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_col() -> Mapped[str]:
    return mapped_column(String(36), primary_key=True, default=_uuid)


def _created_col() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


# --- Enums ---------------------------------------------------------------

class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    DONE = "done"


# --- Entities ------------------------------------------------------------

class Store(Base):
    """Tenant root. Not itself store_id-scoped (it *is* the tenant)."""

    __tablename__ = "stores"

    id: Mapped[str] = _uuid_col()
    store_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    admin_username: Mapped[str] = mapped_column(String(100), nullable=False)
    admin_password_hash: Mapped[str] = mapped_column(String(200), nullable=False)  # bcrypt [SEC-02]
    created_at: Mapped[datetime] = _created_col()

    __table_args__ = (UniqueConstraint("store_code", name="uq_store_code"),)


class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[str] = _uuid_col()
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # >= 0 [BR-C09]
    description: Mapped[str | None] = mapped_column(String(1000))
    category: Mapped[str | None] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = _created_col()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # soft delete [SEC-13]

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_menu_price_nonneg"),
        Index("ix_menu_store", "store_id"),
        Index("ix_menu_store_active", "store_id", "deleted_at"),
    )


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[str] = _uuid_col()
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), nullable=False)
    table_no: Mapped[int] = mapped_column(Integer, nullable=False)
    table_password_hash: Mapped[str] = mapped_column(String(200), nullable=False)  # bcrypt [SEC-02]
    created_at: Mapped[datetime] = _created_col()

    __table_args__ = (
        UniqueConstraint("store_id", "table_no", name="uq_table_store_no"),
        Index("ix_table_store", "store_id"),
    )


class TableSession(Base):
    __tablename__ = "table_sessions"

    id: Mapped[str] = _uuid_col()
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), nullable=False)
    table_id: Mapped[str] = mapped_column(String(36), ForeignKey("tables.id"), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(String(20), default=SessionStatus.ACTIVE, nullable=False)
    session_token: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = _created_col()
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    orders: Mapped[list["Order"]] = relationship(back_populates="session")

    __table_args__ = (
        Index("ix_session_store", "store_id"),
        # At most one ACTIVE session per table (partial unique). [functional-design]
        Index(
            "uq_active_session_per_table",
            "table_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = _uuid_col()
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), nullable=False)
    table_id: Mapped[str] = mapped_column(String(36), ForeignKey("tables.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("table_sessions.id"), nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)  # session-scoped sequence
    items: Mapped[list] = mapped_column(JSON, nullable=False)  # snapshot: name/qty/unit_price
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(String(20), default=OrderStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = _created_col()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # soft delete [SEC-13]

    session: Mapped["TableSession"] = relationship(back_populates="orders")

    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_order_total_nonneg"),
        UniqueConstraint("session_id", "order_no", name="uq_order_session_no"),
        Index("ix_order_store", "store_id"),
        Index("ix_order_session", "session_id"),
    )


class OrderHistory(Base):
    """Isomorphic to Order; rows are moved here when a session closes."""

    __tablename__ = "order_history"

    id: Mapped[str] = _uuid_col()
    store_id: Mapped[str] = mapped_column(String(36), nullable=False)
    table_id: Mapped[str] = mapped_column(String(36), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    original_order_id: Mapped[str] = mapped_column(String(36), nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    items: Mapped[list] = mapped_column(JSON, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moved_at: Mapped[datetime] = _created_col()

    __table_args__ = (
        Index("ix_history_store", "store_id"),
        Index("ix_history_session", "session_id"),
    )
