# =========================
# Project Makefile (clean)
# =========================

PY ?= python
DC ?= docker compose

COMPOSE_DEV  ?= docker-compose.dev.yml
COMPOSE_PROD ?= docker-compose.yml

# Allow overriding DB for psql-prod (e.g., make psql-prod DB=appdb_restore)
DB ?=

# -------- Help --------
.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<TARGET>\033[0m\n\nTargets:\n"} /^[a-zA-Z0-9_%-]+:.*##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ----- Bare-metal -----
.PHONY: venv run-api run-frontend test lint fmt migrate upgrade
venv: ## Create venv and install dependencies
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e ./backend[dev] && pip install streamlit

run-api: ## Run FastAPI locally (reload)
	. .venv/bin/activate && uvicorn backend.app.main:app --reload --port $${API_PORT:-8000}

run-frontend: ## Run Streamlit locally
	. .venv/bin/activate && streamlit run frontend/app.py --server.port $${FRONTEND_PORT:-8501}

test: ## Run tests
	. .venv/bin/activate && pytest -q

lint: ## Ruff check
	. .venv/bin/activate && ruff check . || true

fmt: ## Ruff format
	. .venv/bin/activate && ruff format .

migrate: ## Alembic autogenerate migration
	. .venv/bin/activate && alembic -c backend/alembic.ini revision --autogenerate -m "auto"

upgrade: ## Alembic upgrade head
	. .venv/bin/activate && alembic -c backend/alembic.ini upgrade head

# ----- Docker (dev) -----
.PHONY: dev up down logs shell
dev: ## Dev: up (foreground, build)
	$(DC) -f $(COMPOSE_DEV) up --build

up: ## Dev: up -d (detached, build)
	$(DC) -f $(COMPOSE_DEV) up -d --build

down: ## Dev: down
	$(DC) -f $(COMPOSE_DEV) down

logs: ## Dev: tail logs
	$(DC) -f $(COMPOSE_DEV) logs -f --tail=200

shell: ## Dev: shell into API container
	$(DC) -f $(COMPOSE_DEV) exec api bash

# ----- Docker (prod-ish) -----
.PHONY: prod prod-down prod-logs validate
prod: ## Prod-ish: up -d (build)
	$(DC) -f $(COMPOSE_PROD) up -d --build --remove-orphans

prod-down: ## Prod-ish: down
	$(DC) -f $(COMPOSE_PROD) down

prod-logs: ## Prod-ish: tail logs
	$(DC) -f $(COMPOSE_PROD) logs -f --tail=200

validate: ## Validate docker-compose.yml
	$(DC) -f $(COMPOSE_PROD) config --quiet && echo "docker-compose.yml is valid."

# ----- Prod DB ops (backup/restore) -----
# Requires pg_backup sidecar + /backups mount as configured in docker-compose.yml
.PHONY: psql-prod backup list-dumps restore-latest swap-restore clean-sql
psql-prod: ## Open psql into DB (default: POSTGRES_DB; override with DB=appdb_restore)
	$(DC) -f $(COMPOSE_PROD) exec db bash -lc '\
	  set -euo pipefail; \
	  USERNAME="$${POSTGRES_USER:-postgres}"; \
	  DBNAME="$${DB:-$${POSTGRES_DB:-}}"; \
	  if [ -z "$$DBNAME" ]; then \
	    echo "POSTGRES_DB not set; defaulting DB to USERNAME=$$USERNAME"; \
	    DBNAME="$$USERNAME"; \
	  fi; \
	  echo "Connecting as $$USERNAME to db=$$DBNAME"; \
	  psql -U "$$USERNAME" -d "$$DBNAME" \
	'

backup: ## Run a backup now (custom-format .dump into ./backups)
	$(DC) -f $(COMPOSE_PROD) exec pg_backup bash -lc '/ops/pg-backup.sh && ls -lh /backups | tail -n 5'

list-dumps: ## List recent dumps on host
	@ls -lh backups | tail -n 10 || true

restore-latest: ## Restore latest .dump into appdb_restore (non-destructive to prod DB)
	$(DC) -f $(COMPOSE_PROD) exec db bash -lc 'set -euo pipefail; FILE=$$(ls -1 /backups/*.dump | tail -n 1); echo "Restoring from: $$FILE"; createdb -U "$$POSTGRES_USER" appdb_restore || true; pg_restore -U "$$POSTGRES_USER" --clean --if-exists -d appdb_restore "$$FILE"; psql -U "$$POSTGRES_USER" -d appdb_restore -c "\dt"'

swap-restore: ## Swap appdb_restore -> production DB name (brief API stop)
	$(DC) -f $(COMPOSE_PROD) stop api; \
	$(DC) -f $(COMPOSE_PROD) exec db bash -lc 'psql -U "$$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "\
	  SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
	  WHERE datname IN ( '\''$$POSTGRES_DB'\'', '\''appdb_restore'\'' ); \
	  ALTER DATABASE \"$$POSTGRES_DB\" RENAME TO appdb_old; \
	  ALTER DATABASE appdb_restore RENAME TO \"$$POSTGRES_DB\"; \
	"'; \
	$(DC) -f $(COMPOSE_PROD) start api; \
	echo "Swapped. Verify app, then optionally clean old DB: docker compose -f $(COMPOSE_PROD) exec db bash -lc '\''dropdb -U \"$$POSTGRES_USER\" appdb_old'\''"

clean-sql: ## Remove legacy .sql dumps (keeping .dump)
	@rm -f backups/*.sql || true && echo "Removed old .sql backups (if any)."

# ----- Convenience aliases -----
.PHONY: up-prod down-prod logs-prod
up-prod: prod ## Alias: prod
down-prod: prod-down ## Alias: prod-down
logs-prod: prod-logs ## Alias: prod-logs

