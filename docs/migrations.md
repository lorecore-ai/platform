# Миграции базы данных

В проекте используется [Alembic](https://alembic.sqlalchemy.org/) для управления миграциями PostgreSQL.

## Настройка

### Переменные окружения

Миграции используют `DATABASE_URL` (как и основное приложение):

```bash
# Локально (postgres на хосте)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

# В Docker (postgres на хосте, доступ к контейнеру)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

# В Docker (postgres на хосте контейнера)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
```

Если `DATABASE_URL` не задан, используется значение по умолчанию:  
`postgresql+asyncpg://postgres:postgres@postgres:5432/postgres`

### Установка зависимостей

```bash
pip install -e .
# или
uv sync
```

## Управление миграциями

### 1. Python-скрипт `scripts/migrate.py`

Скрипт предоставляет удобный интерфейс:

```bash
# Применить все миграции
python scripts/migrate.py up

# Применить до конкретной ревизии
python scripts/migrate.py up --revision abc123

# Откатить последнюю миграцию
python scripts/migrate.py down

# Откатить до конкретной ревизии
python scripts/migrate.py down --revision abc123

# Создать миграцию (автогенерация по моделям)
python scripts/migrate.py create "add users table"

# Создать пустую миграцию
python scripts/migrate.py create "custom migration" --no-autogenerate

# Текущая версия схемы
python scripts/migrate.py current

# История миграций
python scripts/migrate.py history
python scripts/migrate.py history --verbose
```

### 2. Makefile

```bash
make migrate-up                    # Применить все миграции
make migrate-down                  # Откатить последнюю
make migrate-create m='описание'   # Создать миграцию
make migrate-current              # Текущая версия
make migrate-history              # История
```

### 3. Прямые команды Alembic

```bash
# Создать миграцию
alembic revision --autogenerate -m "описание"

# Применить миграции
alembic upgrade head

# Откатить последнюю
alembic downgrade -1

# Откатить до конкретной ревизии
alembic downgrade <revision_id>

# Текущая версия
alembic current

# История
alembic history

# Офлайн-режим (генерирует SQL без подключения)
alembic upgrade head --sql
```

## Структура файлов

```
alembic/
├── env.py          # Конфигурация окружения (async, импорт моделей)
├── script.py.mako  # Шаблон для новых миграций
└── versions/       # Файлы миграций
    └── xxx_revision_message.py

alembic.ini         # Конфигурация Alembic
scripts/migrate.py  # CLI для миграций
```

## Workflow при изменении моделей

1. **Изменить модель** в `app/modules/*/models.py`.

2. **Создать миграцию**:
   ```bash
   python scripts/migrate.py create "add column X to agents"
   ```

3. **Проверить сгенерированный файл** в `alembic/versions/` — автогенерация может пропустить некоторые изменения (например, переименование колонок).

4. **Применить миграцию**:
   ```bash
   python scripts/migrate.py up
   ```

5. **При необходимости откатить**:
   ```bash
   python scripts/migrate.py down
   ```

## Запуск миграций перед стартом приложения

В production рекомендуется применять миграции при деплое:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Или в Docker:

```dockerfile
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Примечания

- **Автогенерация** сравнивает текущие модели с очередью миграций и создаёт diff. Не все изменения (например, переименование колонки) могут быть обнаружены автоматически.
- **Async** — миграции выполняются с async-движком PostgreSQL (`asyncpg`).
- **Все модели** должны быть импортированы в `alembic/env.py` для корректной работы autogenerate.
