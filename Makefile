COMPOSE ?= docker compose

.PHONY: help init build up down logs ps check test lint format verify smoke migrations migrate superuser shell

help:
	@echo "init        Copy .env.example once (keeps an existing .env)"
	@echo "build/up    Build the shared image / start app and database"
	@echo "verify      Check Django, migrations, lint, formatting and PostgreSQL tests"
	@echo "smoke       Probe a running app (run make up first)"
	@echo "migrations  Generate migrations; coordinate with the database owner first"
	@echo "migrate     Apply committed migrations"
	@echo "format      Format Python code"
	@echo "logs/ps     View service logs/status"
	@echo "down        Stop services; keep database data"

init:
	@test -f .env || cp .env.example .env

build:
	$(COMPOSE) build backend

up:
	$(COMPOSE) up --build -d --wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

check:
	$(COMPOSE) run --rm -T backend python backend/manage.py check
	$(COMPOSE) run --rm -T backend python backend/manage.py makemigrations --check --dry-run

test:
	$(COMPOSE) run --rm -T backend python backend/manage.py test backend --top-level-directory backend --noinput --verbosity 2

lint:
	$(COMPOSE) run --rm -T --no-deps backend ruff check backend scripts
	$(COMPOSE) run --rm -T --no-deps backend ruff format --check backend scripts

format:
	$(COMPOSE) run --rm -T --no-deps backend ruff format backend scripts

verify:
	$(MAKE) check
	$(MAKE) lint
	$(MAKE) test

smoke:
	$(COMPOSE) exec -T backend python scripts/smoke.py

migrations:
	$(COMPOSE) run --rm backend python backend/manage.py makemigrations

migrate:
	$(COMPOSE) run --rm backend python backend/manage.py migrate

superuser:
	$(COMPOSE) run --rm backend python backend/manage.py createsuperuser

shell:
	$(COMPOSE) run --rm backend python backend/manage.py shell
