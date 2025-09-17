PY?=python
DC?=docker compose

# ----- Bare-metal -----
.PHONY: venv run-api run-frontend test lint fmt migrate upgrade
venv:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e ./backend[dev] && pip install streamlit

run-api:
	. .venv/bin/activate && uvicorn backend.app.main:app --reload --port $${API_PORT:-8000}

run-frontend:
	. .venv/bin/activate && streamlit run frontend/app.py --server.port $${FRONTEND_PORT:-8501}

test:
	. .venv/bin/activate && pytest -q

lint:
	. .venv/bin/activate && ruff check . || true

fmt:
	. .venv/bin/activate && ruff format .

migrate:
	. .venv/bin/activate && alembic -c backend/alembic.ini revision --autogenerate -m "auto"

upgrade:
	. .venv/bin/activate && alembic -c backend/alembic.ini upgrade head

# ----- Docker (dev) -----
.PHONY: dev up down logs shell
dev:
	$(DC) -f docker-compose.dev.yml up --build

up:
	$(DC) -f docker-compose.dev.yml up -d --build

down:
	$(DC) -f docker-compose.dev.yml down

logs:
	$(DC) -f docker-compose.dev.yml logs -f --tail=200

shell:
	$(DC) -f docker-compose.dev.yml exec api bash

# ----- Docker (prod-ish) -----
.PHONY: prod prod-down
prod:
	$(DC) -f docker-compose.yml up -d --build

prod-down:
	$(DC) -f docker-compose.yml down
