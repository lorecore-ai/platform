# Миграции базы данных

В проекте используется [Alembic](https://alembic.sqlalchemy.org/) для управления миграциями PostgreSQL.

Миграции **запускаются только вручную** — это снижает риск случайного повреждения production БД при деплое.

## Обязательно перед стартом приложения

Перед запуском приложения (локально или в production) нужно применить все миграции:

```bash
python scripts/migrate.py up
# или
make migrate-up
```

## Проверка статуса

Текущая версия схемы в БД:

```bash
python scripts/migrate.py current
# или
make migrate-current
```

Пустой вывод — миграции ещё не применялись. Пример: `001 (head)`.

История миграций:

```bash
python scripts/migrate.py history
make migrate-history
python scripts/migrate.py history -v   # подробно
```

Версия хранится в таблице `alembic_version`.

## Удалённый запуск

Для production или удалённой БД задайте `DATABASE_URL`:

```bash
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname" python scripts/migrate.py up
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname" python scripts/migrate.py current
```

В Docker (backend в той же сети, что и postgres):

```bash
docker compose -f infra/docker/docker-compose.yml exec backend python scripts/migrate.py up
docker compose -f infra/docker/docker-compose.yml exec backend python scripts/migrate.py current
```

## Настройка

### Переменные окружения

Миграции используют `DATABASE_URL` (как и приложение):

```bash
# Локально (postgres на хосте)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

# Docker (postgres доступен по имени сервиса)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgres:5432/postgres"
```

По умолчанию:  
`postgresql+asyncpg://postgres:postgres@postgres:5432/postgres`

### Зависимости

```bash
pip install -e .
# или
uv sync
```

## Команды

### scripts/migrate.py

```bash
python scripts/migrate.py up              # Применить все миграции схемы
python scripts/migrate.py up -r abc123   # До конкретной ревизии
python scripts/migrate.py production      # Схема + данные (для продакшена)
python scripts/migrate.py down            # Откатить последнюю
python scripts/migrate.py down -r abc123 # Откатить до ревизии
python scripts/migrate.py current         # Текущая версия
python scripts/migrate.py history        # История

python scripts/migrate.py create "описание"           # Создать миграцию (автогенерация)
python scripts/migrate.py create "описание" --no-autogenerate  # Пустая миграция
```

### Makefile

```bash
make migrate-up
make migrate-down
make migrate-current
make migrate-history
make migrate-create m='описание'
```

### Alembic напрямую

```bash
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
alembic upgrade head --sql   # Только SQL, без выполнения
```

## Структура

```
alembic/
├── versions/       # Миграции схемы (DDL)
│   ├── 001_initial.py
│   ├── 002_add_user_email.py
│   └── 003_create_orders.py
├── env.py          # Окружение (async, импорт моделей)
└── script.py.mako  # Шаблон миграций

migrations/
├── __init__.py
├── runner.py       # Запуск схемы + данных
└── data_migrations/   # Миграции данных (DML)
    └── 001_migrate_user_data.py

alembic.ini         # Конфиг Alembic
scripts/migrate.py  # CLI
scripts/db_health_check.py  # Проверка БД после миграций
```

### Разделение схемы и данных

- **Миграции схемы (alembic/versions/)** — только DDL: CREATE, ALTER, DROP. Управляются Alembic.
- **Миграции данных (migrations/data_migrations/)** — только DML: INSERT, UPDATE. Каждый модуль должен содержать функцию `migrate()`.

Полная миграция для продакшена: `python scripts/migrate.py production`

## Workflow при изменении моделей

1. Изменить модель в `app/modules/*/models.py`.

2. Создать миграцию:
   ```bash
   python scripts/migrate.py create "add column X to agents"
   ```

3. Проверить файл в `alembic/versions/` — автогенерация может пропустить переименования и т.п.

4. Применить:
   ```bash
   python scripts/migrate.py up
   ```

5. При необходимости откатить:
   ```bash
   python scripts/migrate.py down
   ```

## Production

Перед деплоем применяйте миграции отдельным шагом:

```bash
# Только схема
python scripts/migrate.py up

# Схема + данные (полный процесс)
python scripts/migrate.py production

# затем
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Или в CI/CD (см. `.github/workflows/deploy.yml`):

```bash
make migrate-up && docker compose up -d backend
```

CI/CD в `main`:
1. `alembic check` и `alembic history` — проверка миграций
2. Бэкап БД (pg_dump)
3. `python -m migrations.runner` — схемы + данные
4. `python scripts/db_health_check.py` — проверка здоровья

## Примечания

- Автогенерация может пропустить некоторые изменения (переименования, enum и т.д.) — проверяйте файлы миграций.
- Используется async-движок PostgreSQL (`asyncpg`).
- Модели импортируются в `alembic/env.py` для autogenerate.
