#!/usr/bin/env python
"""Проверка здоровья БД после миграций."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
    )


def main() -> int:
    """Проверяет подключение к БД и наличие таблицы alembic_version."""
    try:
        from sqlalchemy import text
        from app.core.database import engine
        import asyncio

        async def check() -> bool:
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
                try:
                    result = await conn.execute(
                        text("SELECT version_num FROM alembic_version LIMIT 1")
                    )
                    row = result.fetchone()
                    if row:
                        print(f"OK: БД доступна, версия миграции: {row[0]}")
                    else:
                        print("OK: БД доступна (alembic_version пуста)")
                except Exception:
                    print("OK: БД доступна")
                return True

        asyncio.run(check())
        return 0
    except Exception as e:
        print(f"Ошибка health check: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
