"""Extend Agent: origin_id, origin_type, nature (rename type), first_name, second_name, email.

Revision ID: 004
Revises: 003
Create Date: 2025-02-14

- type -> nature (column rename, enum agenttype unchanged)
- name -> first_name, second_name
- Add email (nullable)
- Add origin_id, origin_type for integration data
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns
    op.add_column("agents", sa.Column("first_name", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("second_name", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("origin_id", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("origin_type", sa.String(64), nullable=True))

    # 2. Migrate name -> first_name, second_name
    op.execute("UPDATE agents SET first_name = COALESCE(name, ''), second_name = COALESCE(second_name, '')")

    # 3. Make first_name, second_name NOT NULL
    op.alter_column("agents", "first_name", nullable=False)
    op.alter_column("agents", "second_name", nullable=False)

    # 4. Rename type -> nature
    op.alter_column(
        "agents",
        "type",
        new_column_name="nature",
    )

    # 5. Drop name
    op.drop_column("agents", "name")

    # 6. Create indexes for origin_id, origin_type
    op.create_index("ix_agents_origin_id", "agents", ["origin_id"])
    op.create_index("ix_agents_origin_type", "agents", ["origin_type"])


def downgrade() -> None:
    op.drop_index("ix_agents_origin_type", "agents")
    op.drop_index("ix_agents_origin_id", "agents")

    op.add_column("agents", sa.Column("name", sa.String(255), nullable=True))
    op.execute("UPDATE agents SET name = TRIM(CONCAT(first_name, ' ', second_name))")
    op.alter_column("agents", "name", nullable=False)

    op.alter_column("agents", "nature", new_column_name="type")

    op.drop_column("agents", "origin_type")
    op.drop_column("agents", "origin_id")
    op.drop_column("agents", "email")
    op.drop_column("agents", "second_name")
    op.drop_column("agents", "first_name")
