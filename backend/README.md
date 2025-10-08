# Meeting Notes Assistant — Backend

## Overview
FastAPI backend for the **Meeting Notes Assistant**. It manages meetings, slide uploads, background processing (ASR/OCR/summarization), and persistence to the database and S3-compatible storage (MinIO in dev).

> **Heads‑up:** Endpoint names changed slightly over sprints. The canonical current routes live under `/v1/…` and are visible in the OpenAPI docs at `/docs` and `/redoc`. If you’re on an older branch, you may still see legacy routes like `/attach-slides`.

## Stack
- **API:** FastAPI + Uvicorn
- **DB:** PostgreSQL (docker) or SQLite (dev/local)
- **Migrations:** Alembic
- **Object Storage:** MinIO (S3 compatible)
- **Async/Jobs (planned):** Celery / RQ or simple background tasks

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (recommended for db + minio + full stack)

## Quickstart (Docker Compose)
1. Copy the sample env and adjust as needed:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env  # if running full stack
   ```
2. Start services:
   ```bash
   docker compose up -d db minio backend
   ```
3. Initialize DB:
   ```bash
   docker compose exec backend bash -lc 'alembic -c backend/alembic.ini upgrade head'
   ```
4. Open API docs: http://127.0.0.1:8000/docs

## Quickstart (Local Python)
```bash
# from repo root
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# configure env
cp backend/.env.example backend/.env
# edit backend/.env as needed

# run migrations
alembic -c backend/alembic.ini upgrade head

# run the api
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

## Configuration
Create `backend/.env` with values similar to:
```ini
# General
APP_ENV=dev
PORT=8000
LOG_LEVEL=INFO

# Database (choose one)
# SQLite (dev quickstart)
DATABASE_URL=sqlite:///./dev.db
# PostgreSQL (docker compose)
# DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/meetings

# S3 / MinIO
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_USE_SSL=false
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
RAW_BUCKET=raw
SLIDES_BUCKET=meeting-slides

# (Optional) CORS to allow local frontend
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501
```
> The backend will lazily ensure the `SLIDES_BUCKET` exists on first use.

## Database Migrations (Alembic)
```bash
# Show current revision
alembic -c backend/alembic.ini current

# Upgrade to latest
alembic -c backend/alembic.ini upgrade head

# Create a new migration (after editing models)
alembic -c backend/alembic.ini revision --autogenerate -m "<message>"
```

## Health & Diagnostics
```bash
curl -s http://127.0.0.1:8000/healthz | jq
```

## Core Endpoints (cheat‑sheet)
> Exact shape depends on branch. Confirm in `/docs`.

- **Health**
  - `GET /healthz` → `{ "status": "ok" }`
- **Meetings** (examples)
  - `POST /v1/meetings` or `POST /v1/meetings/start` → create a new meeting (returns `id`)
  - `GET  /v1/meetings` → list meetings
  - `POST /v1/meetings/{meeting_id}/process` → trigger ASR/OCR/summarization
- **Slides** (current canonical)
  - `POST /v1/meetings/{meeting_id}/slides` (multipart, field name `files`) → upload 1..N files

### cURL examples
Create a meeting:
```bash
curl -s -X POST http://127.0.0.1:8000/v1/meetings | jq
# → { "id": 42, ... }
```
Upload slides (multi-file):
```bash
MEETING_ID=42
curl -s -X POST "http://127.0.0.1:8000/v1/meetings/$MEETING_ID/slides"   -F "files=@/path/to/slide1.pdf"   -F "files=@/path/to/slide2.png" | jq
```
Trigger processing:
```bash
curl -s -X POST "http://127.0.0.1:8000/v1/meetings/$MEETING_ID/process" | jq
```

> **Legacy note:** On older branches you may see `POST /v1/meetings/{id}/attach-slides` with field `file` (singular). Prefer the canonical plural `files` route going forward.

## MinIO quick notes
- Server: `http://127.0.0.1:9000` (no SSL in dev)
- Credentials: `minio / minio123` (from `.env`)
- Buckets used: `raw`, `meeting-slides`

## Testing
```bash
pytest -q
```

## Project Layout (backend)
```
backend/
  app/
    main.py
    routers/
      slides.py
    models/  # SQLAlchemy models
    services/
    ...
  alembic.ini
  alembic/
  requirements.txt
  .env.example
```

## Roadmap (high level)
- Whisper/AssemblyAI/OpenAI transcription providers
- Tesseract/Textract OCR for slides
- GPT‑4o (or configured LLM) for summaries & action items
- Job queue + status endpoints & telemetry

## License
Internal/MVP. Replace with your preferred license for distribution.
