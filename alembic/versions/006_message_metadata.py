"""Add metadata JSONB column to messages table.

Revision ID: 006
Revises: 005
Create Date: 2026-02-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "006"
down_revision: Union[str, Sequence[str], None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("metadata", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "metadata")
