#!/usr/bin/env python
"""CLI для управления миграциями Alembic."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_alembic(args: list[str]) -> int:
    """Запуск alembic с переданными аргументами."""
    env = os.environ.copy()
    if "DATABASE_URL" not in env:
        env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
    cmd = [sys.executable, "-m", "alembic"] + args
    return subprocess.run(cmd, env=env, cwd=PROJECT_ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Управление миграциями базы данных",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python scripts/migrate.py up              # Применить все миграции
  python scripts/migrate.py up --revision head
  python scripts/migrate.py down            # Откатить последнюю миграцию
  python scripts/migrate.py create "add users table"
  python scripts/migrate.py current         # Текущая версия
  python scripts/migrate.py history         # История миграций
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # up - применить миграции
    up_parser = subparsers.add_parser("up", help="Применить миграции")
    up_parser.add_argument(
        "--revision",
        "-r",
        default="head",
        help="Целевая ревизия (по умолчанию: head)",
    )
    up_parser.set_defaults(
        handler=lambda ns: run_alembic(["upgrade", ns.revision])
    )

    # down - откатить миграции
    down_parser = subparsers.add_parser("down", help="Откатить миграции")
    down_parser.add_argument(
        "--revision",
        "-r",
        default="-1",
        help="Целевая ревизия (по умолчанию: -1 — последняя)",
    )
    down_parser.set_defaults(
        handler=lambda ns: run_alembic(["downgrade", ns.revision])
    )

    # create - создать миграцию
    create_parser = subparsers.add_parser(
        "create",
        help="Создать автосгенерированную миграцию",
    )
    create_parser.add_argument(
        "message",
        help="Описание миграции",
    )
    create_parser.add_argument(
        "--autogenerate",
        "-a",
        action="store_true",
        default=True,
        help="Автогенерация по моделям (по умолчанию: вкл)",
    )
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_false",
        dest="autogenerate",
        help="Пустая миграция без автогенерации",
    )
    create_parser.set_defaults(
        handler=lambda ns: run_alembic(
            ["revision", "--autogenerate", "-m", ns.message]
            if ns.autogenerate
            else ["revision", "-m", ns.message]
        )
    )

    # current - текущая версия
    current_parser = subparsers.add_parser(
        "current",
        help="Показать текущую версию схемы",
    )
    current_parser.set_defaults(
        handler=lambda _: run_alembic(["current"])
    )

    # history - история
    history_parser = subparsers.add_parser(
        "history",
        help="Показать историю миграций",
    )
    history_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Подробный вывод",
    )
    history_parser.set_defaults(
        handler=lambda ns: run_alembic(
            ["history", "--verbose"] if ns.verbose else ["history"]
        )
    )

    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
