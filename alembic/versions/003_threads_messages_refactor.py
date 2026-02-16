"""Refactor threads and messages: many-to-many agents, metadata, message agent_id.

Revision ID: 003
Revises: 002
Create Date: 2025-02-14

- threads: agent_id -> many-to-many via thread_agents, add metadata JSONB
- messages: add agent_id FK to agents
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Create thread_agents association table (if not exists)
    if "thread_agents" not in tables:
        op.create_table(
            "thread_agents",
            sa.Column("thread_id", UUID(as_uuid=True), sa.ForeignKey("threads.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
        )

    # 2. Migrate thread.agent_id -> thread_agents (skip if threads has no agent_id)
    thread_columns = [c["name"] for c in inspector.get_columns("threads")]
    if "agent_id" in thread_columns:
        op.execute("""
            INSERT INTO thread_agents (thread_id, agent_id)
            SELECT id, agent_id FROM threads WHERE agent_id IS NOT NULL
            ON CONFLICT (thread_id, agent_id) DO NOTHING
        """)

    # 3. Add metadata to threads
    if "metadata" not in [c["name"] for c in inspector.get_columns("threads")]:
        op.add_column("threads", sa.Column("metadata", JSONB, nullable=True))

    # 4. Drop agent_id from threads
    if "agent_id" in [c["name"] for c in inspector.get_columns("threads")]:
        op.drop_column("threads", "agent_id")
        inspector = sa.inspect(op.get_bind())  # refresh after drop

    # 5. Add agent_id to messages (nullable for migration)
    msg_columns = [c["name"] for c in inspector.get_columns("messages")]
    if "agent_id" not in msg_columns:
        op.add_column(
            "messages",
            sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=True),
        )

    # 6. Migrate: set agent_id for existing messages
    # assistant -> thread's agent; user -> tenant's human or thread's agent as fallback
    op.execute("""
        UPDATE messages m SET agent_id = (
            SELECT ta.agent_id FROM thread_agents ta
            WHERE ta.thread_id = m.thread_id
            LIMIT 1
        )
        WHERE m.role = 'assistant'
    """)
    op.execute("""
        UPDATE messages m SET agent_id = (
            SELECT a.id FROM agents a
            JOIN threads t ON t.tenant_id = a.tenant_id
            WHERE t.id = m.thread_id AND a.type = 'human'
            LIMIT 1
        )
        WHERE m.role = 'user' AND m.agent_id IS NULL
    """)
    # Fallback for user messages: use thread's agent if no human found
    op.execute("""
        UPDATE messages m SET agent_id = (
            SELECT ta.agent_id FROM thread_agents ta WHERE ta.thread_id = m.thread_id LIMIT 1
        )
        WHERE m.agent_id IS NULL
    """)

    # 7. Make agent_id NOT NULL
    op.alter_column(
        "messages",
        "agent_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )
    idx_names = [i["name"] for i in sa.inspect(op.get_bind()).get_indexes("messages")]
    if "ix_messages_agent_id" not in idx_names:
        op.create_index("ix_messages_agent_id", "messages", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_agent_id", "messages")

    op.add_column(
        "threads",
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=True),
    )
    op.execute("""
        UPDATE threads t SET agent_id = (
            SELECT ta.agent_id FROM thread_agents ta WHERE ta.thread_id = t.id LIMIT 1
        )
    """)
    op.alter_column("threads", "agent_id", nullable=False)

    op.drop_column("threads", "metadata")
    op.drop_column("messages", "agent_id")
    op.drop_table("thread_agents")
