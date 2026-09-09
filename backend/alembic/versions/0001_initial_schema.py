"""initial schema — shared domain entities

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-08

Creates the 6 core entities with UUID PKs, store_id scoping, soft-delete columns,
composite indexes, and the partial-unique active-session-per-table index. [NFR-M2]
Downgrade drops everything (supports RES-04 rollback).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("store_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("admin_username", sa.String(length=100), nullable=False),
        sa.Column("admin_password_hash", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_code", name="uq_store_code"),
    )

    op.create_table(
        "menus",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("store_id", sa.String(length=36), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=1000)),
        sa.Column("category", sa.String(length=100)),
        sa.Column("image_url", sa.String(length=500)),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("price >= 0", name="ck_menu_price_nonneg"),
    )
    op.create_index("ix_menu_store", "menus", ["store_id"])
    op.create_index("ix_menu_store_active", "menus", ["store_id", "deleted_at"])

    op.create_table(
        "tables",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("store_id", sa.String(length=36), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("table_no", sa.Integer(), nullable=False),
        sa.Column("table_password_hash", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "table_no", name="uq_table_store_no"),
    )
    op.create_index("ix_table_store", "tables", ["store_id"])

    op.create_table(
        "table_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("store_id", sa.String(length=36), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("table_id", sa.String(length=36), sa.ForeignKey("tables.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("session_token", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_session_store", "table_sessions", ["store_id"])
    # At most one ACTIVE session per table. [functional-design]
    op.create_index(
        "uq_active_session_per_table",
        "table_sessions",
        ["table_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("store_id", sa.String(length=36), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("table_id", sa.String(length=36), sa.ForeignKey("tables.id"), nullable=False),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("table_sessions.id"), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("total >= 0", name="ck_order_total_nonneg"),
        sa.UniqueConstraint("session_id", "order_no", name="uq_order_session_no"),
    )
    op.create_index("ix_order_store", "orders", ["store_id"])
    op.create_index("ix_order_session", "orders", ["session_id"])

    op.create_table(
        "order_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("table_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("original_order_id", sa.String(length=36), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_closed_at", sa.DateTime(timezone=True)),
        sa.Column("moved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_history_store", "order_history", ["store_id"])
    op.create_index("ix_history_session", "order_history", ["session_id"])


def downgrade() -> None:
    op.drop_table("order_history")
    op.drop_table("orders")
    op.drop_index("uq_active_session_per_table", table_name="table_sessions")
    op.drop_table("table_sessions")
    op.drop_table("tables")
    op.drop_table("menus")
    op.drop_table("stores")
