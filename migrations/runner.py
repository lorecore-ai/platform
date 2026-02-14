"""
Запуск миграций: схемы (DDL) и данных (DML).

Схемы — через Alembic.
Данные — через модули в migrations/data_migrations/ с функцией migrate().
"""
import importlib
import os
import sys
from pathlib import Path

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _default_database_url() -> str:
    return "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"


def run_schema_migrations() -> None:
    """Миграции схемы (DDL) через Alembic."""
    os.chdir(PROJECT_ROOT)
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = _default_database_url()

    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def run_data_migrations() -> None:
    """Миграции данных (DML) — отдельно от схемы."""
    data_migrations_dir = PROJECT_ROOT / "migrations" / "data_migrations"

    if not data_migrations_dir.exists():
        return

    for filename in sorted(os.listdir(data_migrations_dir)):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"migrations.data_migrations.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "migrate"):
                    print(f"Запуск миграции данных: {filename}")
                    module.migrate()
            except Exception as e:
                print(f"Ошибка в миграции данных {filename}: {e}", file=sys.stderr)
                raise


def migrate_production() -> None:
    """Полный процесс миграции для продакшена."""
    print("1. Применение миграций схемы...")
    run_schema_migrations()

    print("2. Применение миграций данных...")
    run_data_migrations()

    print("✓ Все миграции применены")


if __name__ == "__main__":
    migrate_production()
