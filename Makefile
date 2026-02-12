# LoreCore Makefile
# Управление миграциями и разработкой

.PHONY: migrate-up migrate-down migrate-create migrate-current migrate-history help

# Переменная окружения для БД (можно переопределить)
DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@postgres:5432/postgres

help:
	@echo "Миграции:"
	@echo "  make migrate-up        - Применить все миграции"
	@echo "  make migrate-down      - Откатить последнюю миграцию"
	@echo "  make migrate-create m='описание' - Создать миграцию"
	@echo "  make migrate-current   - Текущая версия"
	@echo "  make migrate-history   - История миграций"

migrate-up:
	DATABASE_URL=$(DATABASE_URL) alembic upgrade head

migrate-down:
	DATABASE_URL=$(DATABASE_URL) alembic downgrade -1

migrate-create:
	@if [ -z "$(m)" ]; then echo "Usage: make migrate-create m='описание миграции'"; exit 1; fi
	DATABASE_URL=$(DATABASE_URL) alembic revision --autogenerate -m "$(m)"

migrate-current:
	DATABASE_URL=$(DATABASE_URL) alembic current

migrate-history:
	DATABASE_URL=$(DATABASE_URL) alembic history --verbose
