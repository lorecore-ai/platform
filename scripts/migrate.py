#!/usr/bin/env python
"""CLI для управления миграциями Alembic."""
import argparse
import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Устанавливаем DATABASE_URL до импорта alembic
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
    )


def get_config():
    """Конфигурация Alembic."""
    from alembic.config import Config

    os.chdir(PROJECT_ROOT)
    config_file = PROJECT_ROOT / "alembic.ini"
    return Config(str(config_file))


def cmd_up(revision: str) -> int:
    """Применить миграции."""
    from alembic import command

    command.upgrade(get_config(), revision)
    return 0


def cmd_down(revision: str) -> int:
    """Откатить миграции."""
    from alembic import command

    command.downgrade(get_config(), revision)
    return 0


def cmd_create(message: str, autogenerate: bool) -> int:
    """Создать миграцию."""
    from alembic import command

    config = get_config()
    if autogenerate:
        command.revision(config, message=message, autogenerate=True)
    else:
        command.revision(config, message=message)
    return 0


def cmd_current() -> int:
    """Текущая версия."""
    from alembic import command

    command.current(get_config())
    return 0


def cmd_history(verbose: bool) -> int:
    """История миграций."""
    from alembic import command

    command.history(get_config(), verbose=verbose)
    return 0


def cmd_production() -> int:
    """Полный процесс миграции для продакшена (схема + данные)."""
    from migrations.runner import migrate_production

    migrate_production()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Управление миграциями базы данных",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python scripts/migrate.py up              # Применить все миграции
  python scripts/migrate.py up --revision head
  python scripts/migrate.py production      # Схема + данные (для продакшена)
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
    up_parser.set_defaults(handler=lambda ns: cmd_up(ns.revision))

    # down - откатить миграции
    down_parser = subparsers.add_parser("down", help="Откатить миграции")
    down_parser.add_argument(
        "--revision",
        "-r",
        default="-1",
        help="Целевая ревизия (по умолчанию: -1 — последняя)",
    )
    down_parser.set_defaults(handler=lambda ns: cmd_down(ns.revision))

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
        handler=lambda ns: cmd_create(ns.message, ns.autogenerate)
    )

    # current - текущая версия
    current_parser = subparsers.add_parser(
        "current",
        help="Показать текущую версию схемы",
    )
    current_parser.set_defaults(handler=lambda _: cmd_current())

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
        handler=lambda ns: cmd_history(ns.verbose)
    )

    # production - полная миграция (схема + данные)
    subparsers.add_parser(
        "production",
        help="Применить схему и миграции данных (для продакшена)",
    ).set_defaults(handler=lambda _: cmd_production())

    args = parser.parse_args()
    try:
        return args.handler(args)
    except ImportError as e:
        print(
            "Ошибка: alembic не установлен. Выполните: pip install -e .",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
