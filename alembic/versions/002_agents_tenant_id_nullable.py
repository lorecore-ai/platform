"""Agents table: tenant_id nullable, drop model/system_prompt.

Revision ID: 002
Revises: 001
Create Date: 2025-02-14

- tenant_id: nullable for platform agents (Assistant, etc.)
- Drop model, system_prompt: align with simplified Agent model
"""
from typing import Sequence, Union

from alembic import op


revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ALTER COLUMN tenant_id DROP NOT NULL")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS model")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS system_prompt")


def downgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN model VARCHAR(255) DEFAULT ''")
    op.execute("ALTER TABLE agents ADD COLUMN system_prompt TEXT DEFAULT ''")
    op.execute("ALTER TABLE agents ALTER COLUMN model SET NOT NULL")
    op.execute("ALTER TABLE agents ALTER COLUMN system_prompt SET NOT NULL")
    op.execute("ALTER TABLE agents ALTER COLUMN tenant_id SET NOT NULL")
