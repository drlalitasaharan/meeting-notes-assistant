# Meeting Notes Assistant — Hybrid Bare‑Metal + Docker Starter

## Quick start (bare‑metal)
```bash
make venv
cp .env.example .env
make run-api
make run-frontend
```
API: http://localhost:8000/docs
Frontend: http://localhost:8501

## Quick start (Docker dev)
```bash
cp .env.example .env
make up
```
Stop: `make down`

## Migrations
- Create: `make migrate`
- Apply:  `make upgrade`
