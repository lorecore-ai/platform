"""Add BaseEntity fields: created_at, updated_at, deleted_at to all entity tables.

Revision ID: 005
Revises: 004
Create Date: 2025-02-14

Tables: agents, tenants, events, integrations get created_at, updated_at, deleted_at.
threads: add deleted_at (created_at, updated_at exist).
messages: add updated_at, deleted_at (created_at exists).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "005"
down_revision: Union[str, Sequence[str], None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_timestamp_columns(table: str) -> None:
    """Add created_at, updated_at, deleted_at to a table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]

    if "created_at" not in cols:
        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    if "updated_at" not in cols:
        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    if "deleted_at" not in cols:
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def upgrade() -> None:
    _add_timestamp_columns("agents")
    _add_timestamp_columns("tenants")
    _add_timestamp_columns("events")
    _add_timestamp_columns("integrations")

    # threads: created_at, updated_at exist; add deleted_at
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "deleted_at" not in [c["name"] for c in inspector.get_columns("threads")]:
        op.add_column("threads", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # messages: created_at exists; add updated_at, deleted_at
    msg_cols = [c["name"] for c in inspector.get_columns("messages")]
    if "updated_at" not in msg_cols:
        op.add_column(
            "messages",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    if "deleted_at" not in msg_cols:
        op.add_column("messages", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for table in ("agents", "tenants", "events", "integrations"):
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")

    op.drop_column("threads", "deleted_at")
    op.drop_column("messages", "deleted_at")
    op.drop_column("messages", "updated_at")
