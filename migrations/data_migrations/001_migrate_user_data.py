"""
Пример миграции данных.

Шаблон для DML-миграций. Используйте sync-движок (psycopg2),
т.к. data migrations выполняют raw SQL батчами.

Переменная DATABASE_URL: для sync замените asyncpg на psycopg2:
  postgresql+psycopg2://user:pass@host:5432/dbname
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os


def _get_sync_url() -> str:
    """Преобразует DATABASE_URL для sync движка (psycopg2)."""
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres",
    )
    # asyncpg -> psycopg2 для sync операций
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def migrate() -> None:
    """
    Миграция данных — пример.

    Обработка батчами для больших таблиц.
    Раскомментируйте и адаптируйте под свои данные.
    """
    engine = create_engine(_get_sync_url())
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()

    try:
        # Пример: обновление данных батчами
        # batch_size = 1000
        # offset = 0
        # while True:
        #     result = session.execute(text("""
        #         SELECT id, old_name FROM users
        #         WHERE new_name IS NULL LIMIT :batch OFFSET :offset
        #     """), {"batch": batch_size, "offset": offset})
        #     rows = result.fetchall()
        #     if not rows:
        #         break
        #     for row in rows:
        #         session.execute(text("""
        #             UPDATE users SET new_name = :name WHERE id = :id
        #         """), {"name": row.old_name, "id": row.id})
        #     session.commit()
        #     offset += batch_size
        #     print(f"Обработано {offset} записей...")
        pass  # Заглушка — нет данных для миграции
    finally:
        session.close()
