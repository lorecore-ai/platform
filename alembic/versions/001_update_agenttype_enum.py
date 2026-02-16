"""Update agenttype enum: main->human, llm->system, add worker.

Revision ID: 001
Revises:
Create Date: 2025-02-12

Исправляет ошибку: invalid input value for enum agenttype: "System"
БД содержит старые значения (main, llm), код ожидает (human, system, worker).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update agenttype enum to human, system, worker."""
    # PostgreSQL: создаём новый enum и мигрируем данные
    op.execute("CREATE TYPE agenttype_new AS ENUM ('human', 'system', 'worker')")

    # Добавляем временную колонку
    op.execute("ALTER TABLE agents ADD COLUMN type_new agenttype_new")

    # Мигрируем: main->human, llm->system, worker->worker
    op.execute("""
        UPDATE agents SET type_new = CASE type::text
            WHEN 'main' THEN 'human'::agenttype_new
            WHEN 'llm' THEN 'system'::agenttype_new
            WHEN 'worker' THEN 'worker'::agenttype_new
            WHEN 'Human' THEN 'human'::agenttype_new
            WHEN 'System' THEN 'system'::agenttype_new
            ELSE 'human'::agenttype_new
        END
    """)

    # Делаем колонку NOT NULL
    op.execute("ALTER TABLE agents ALTER COLUMN type_new SET NOT NULL")

    # Удаляем старую колонку и переименовываем
    op.execute("ALTER TABLE agents DROP COLUMN type")
    op.execute("ALTER TABLE agents RENAME COLUMN type_new TO type")

    # Удаляем старый enum и переименовываем новый
    op.execute("DROP TYPE agenttype")
    op.execute("ALTER TYPE agenttype_new RENAME TO agenttype")


def downgrade() -> None:
    """Revert to old agenttype enum (main, llm, worker)."""
    op.execute("CREATE TYPE agenttype_old AS ENUM ('main', 'llm', 'worker')")

    op.execute("ALTER TABLE agents ADD COLUMN type_old agenttype_old")

    op.execute("""
        UPDATE agents SET type_old = CASE type::text
            WHEN 'human' THEN 'main'::agenttype_old
            WHEN 'system' THEN 'llm'::agenttype_old
            WHEN 'worker' THEN 'worker'::agenttype_old
            ELSE 'main'::agenttype_old
        END
    """)

    op.execute("ALTER TABLE agents ALTER COLUMN type_old SET NOT NULL")
    op.execute("ALTER TABLE agents DROP COLUMN type")
    op.execute("ALTER TABLE agents RENAME COLUMN type_old TO type")

    op.execute("DROP TYPE agenttype")
    op.execute("ALTER TYPE agenttype_old RENAME TO agenttype")
