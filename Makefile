# LoreCore Makefile
# Database migrations and development
# Supports Windows (cmd) and Unix

.PHONY: migrate-up migrate-down migrate-create migrate-current migrate-history help

# Database env var (can override)
# localhost:5434 = postgres in Docker, port exposed. Use postgres:5432 from inside container
DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@localhost:5434/postgres

# Windows: set VAR=value && command | Unix: VAR=value command
ifeq ($(OS),Windows_NT)
  SET_ENV = set "DATABASE_URL=$(DATABASE_URL)" &&
  PYTHON ?= python
else
  SET_ENV = DATABASE_URL="$(DATABASE_URL)"
  PYTHON ?= python
endif

help:
	@echo "Migrations:"
	@echo "  make migrate-up        	- Apply schema migrations"
	@echo "  make migrate-production 	- Schema + data (production)"
	@echo "  make migrate-down      	- Rollback last migration"
	@echo "  make migrate-create m='description' - Create migration"
	@echo "  make migrate-current   	- Current version"
	@echo "  make migrate-history   	- Migration history"

migrate-up:
	$(SET_ENV) $(PYTHON) scripts/migrate.py up

migrate-production:
	$(SET_ENV) $(PYTHON) -m migrations.runner

migrate-down:
	$(SET_ENV) alembic downgrade -1

migrate-create:
	@if [ -z "$(m)" ]; then echo "Usage: make migrate-create m='migration description'"; exit 1; fi
	$(SET_ENV) alembic revision --autogenerate -m "$(m)"

migrate-current:
	$(SET_ENV) alembic current

migrate-history:
	$(SET_ENV) alembic history --verbose
