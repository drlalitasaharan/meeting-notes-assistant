
# RUNBOOK — Meeting Notes Assistant (Local & Dev)

> This runbook replaces the old root `runback.md` and aligns the project with the new queue-based pipeline (Redis + RQ), `/notes` endpoint, OCR + summarization, MinIO fallback, Prometheus metrics, and CI smoke tests.

---

## 0) Prerequisites

- **Docker & Docker Compose**
- **Python 3.11+** (only if you also want to run pieces locally)
- Per-service env files:
  - `backend/.env` (copy from `backend/.env.example`)
  - `frontend/.env` (copy from `frontend/.env.example`)
- Optional **root** `.env` used only for Compose variable substitution (e.g., `${DB_USER}`)

### One-time setup
```bash
# Service envs
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# (Optional) local runs
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

---

## 1) Services (root `docker-compose.yml`)

- **api** – FastAPI backend
- **frontend** – Streamlit UI
- **db** – PostgreSQL 16
- **pg_backup** – simple periodic backup job
- **redis** – Redis 7 for job queue
- **worker** – RQ worker processing background jobs

### Bring everything up
```bash
docker compose up -d --build redis db api worker frontend
```

### Tail logs
```bash
docker compose logs -f db redis api worker frontend
```

### Health check
```bash
curl -s http://127.0.0.1:8000/healthz | jq .
```
Expected: `{ "status": "ok" }`

---

## 2) Database Migrations (Alembic)

Run when models change (e.g., Transcript/Summary).

```bash
# Show current revision
alembic -c backend/alembic.ini current

# Create a migration (after editing models)
alembic -c backend/alembic.ini revision --autogenerate -m "notes tables"

# Apply migrations
alembic -c backend/alembic.ini upgrade head
```

Or from the api container:
```bash
docker compose exec api bash -lc 'alembic -c backend/alembic.ini upgrade head'
```

---

## 3) Queue-Based Processing (Redis + RQ)

### Enqueue
```bash
# Create a meeting
MID=$(curl -s -X POST http://127.0.0.1:8000/v1/meetings | jq -r '.id')

# Attach a small file (text works; images give OCR)
echo "slide-1: hello world" > /tmp/slide1.txt
curl -s -X POST "http://127.0.0.1:8000/v1/meetings/$MID/slides"   -F "files=@/tmp/slide1.txt" | jq .

# Enqueue processing
JOB=$(curl -s -X POST "http://127.0.0.1:8000/v1/meetings/$MID/process" | jq -r '.job_id')
echo "$JOB"
```

### Poll status
```bash
curl -s "http://127.0.0.1:8000/v1/meetings/jobs/$JOB" | jq .
```
Statuses: `queued | started | finished | failed`

### Fetch notes (Transcript + Summary)
```bash
curl -s "http://127.0.0.1:8000/v1/meetings/$MID/notes" | jq .
```

---

## 4) Frontend (Streamlit)

Ensure `frontend/.env` points to the backend:
```ini
BACKEND_BASE_URL=http://127.0.0.1:8000
```

Run with Compose:
```bash
docker compose up -d frontend
```

Or locally:
```bash
source .venv/bin/activate
streamlit run frontend/streamlit_app.py --server.port 3000
```

Open **http://127.0.0.1:3000**. Meeting page shows:
- “Process (enqueue)” button
- Latest **Summary**
- Transcript **snippet**

---

## 5) OCR (Slides → Text)

- Image formats (`.png`, `.jpg`, `.jpeg`, `.tif`) OCR via `pytesseract`.
- PDFs require a PDF→images step (e.g., `pdf2image`)—add later if needed.
- OCR output persisted as a **Transcript** row.

If using MinIO/S3 storage (see §7), worker downloads to temp before OCR.

---

## 6) Summarization (LLM Hook)

- Summarizes the latest transcript and writes a **Summary** row.
- Swap providers easily (OpenAI/Azure/etc.).
- Configure keys in `backend/.env` (e.g., `OPENAI_API_KEY`) and update the summarizer.

---

## 7) MinIO / S3 Storage (with local fallback)

- Default dev: local `storage/{meeting_id}/` for slides.
- Enable object store by setting `USE_OBJECT_STORAGE=true` in `backend/.env`.

Example:
```ini
USE_OBJECT_STORAGE=false
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_USE_SSL=false
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
RAW_BUCKET=raw
SLIDES_BUCKET=meeting-slides
```
When enabled: uploads go to `s3://{SLIDES_BUCKET}/{meeting_id}/...`.

---

## 8) Prometheus Metrics

- Endpoint: **`GET /metrics`**
- Includes:
  - `http_requests_total{method,path,status}`
  - `http_request_duration_seconds{method,path}`
  - `job_duration_seconds{job}`
  - `job_count_total{job,status}`

Quick check:
```bash
curl -s http://127.0.0.1:8000/metrics | head -n 30
```

---

## 9) Backups

- `pg_backup` runs `/ops/pg-backup.sh` on a schedule (default daily).
- Dumps in `./backups`.

Manual backup:
```bash
docker compose run --rm pg_backup bash -lc "/ops/pg-backup.sh"
ls -l ./backups
```

Restore outline:
```bash
docker compose stop api worker
# Drop/create DB and restore from ./backups/<chosen dump>
docker compose up -d api worker
```

---

## 10) CI Smoke Test

Script `ops/smoke.sh` does:
- health check
- create meeting
- upload slide
- enqueue job
- poll status
- fetch notes

Local:
```bash
bash ops/smoke.sh http://127.0.0.1:8000
```

GitHub Actions snippet:
```yaml
- run: docker compose up -d --build redis db api worker
- run: bash ops/smoke.sh http://127.0.0.1:8000
```

---

## 11) Frequently Used Commands

```bash
# Compose lifecycle
docker compose up -d --build
docker compose ps
docker compose logs -f api worker redis db frontend
docker compose stop
docker compose down -v

# API quick test
curl -s http://127.0.0.1:8000/docs > /dev/null && echo "API docs reachable"

# Meetings flow
MID=$(curl -s -X POST http://127.0.0.1:8000/v1/meetings | jq -r '.id')
curl -s -X POST "http://127.0.0.1:8000/v1/meetings/$MID/slides" -F "files=@/tmp/slide1.txt" | jq .
JOB=$(curl -s -X POST "http://127.0.0.1:8000/v1/meetings/$MID/process" | jq -r '.job_id')
curl -s "http://127.0.0.1:8000/v1/meetings/jobs/$JOB" | jq .
curl -s "http://127.0.0.1:8000/v1/meetings/$MID/notes" | jq .

# Alembic
alembic -c backend/alembic.ini current
alembic -c backend/alembic.ini upgrade head
```

---

## 12) Troubleshooting

- **CORS**: ensure `CORS_ORIGINS` in `backend/.env` includes your frontend origin.
- **Worker idle**: check `redis` & `worker` logs; `RQ_WORKER_QUEUES=default`; Redis host should be `redis`.
- **Migrations**: verify `DATABASE_URL` and run `alembic upgrade head`.
- **MinIO**: check credentials & `MINIO_ENDPOINT`; set `USE_OBJECT_STORAGE=false` to fall back to local.
- **OCR empty**: ensure `pytesseract` in the backend image; add PDF→image conversion for PDFs.
- **Metrics**: confirm `/metrics` reachable; verify Prometheus scrape config.

---

## 13) Ports

- **API**: 8000
- **Frontend**: 8501 (or `${FRONTEND_PORT:-8501}`)
- **Redis**: 6379
- **Postgres**: internal only
- **Metrics**: `GET /metrics` on the API

---

## 14) Env Cheatsheet

**backend/.env**
```ini
APP_ENV=dev
PORT=8000
LOG_LEVEL=INFO

DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/meetings
# or: sqlite:///./dev.db

# Redis / RQ
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
RQ_WORKER_QUEUES=default

# Object store
USE_OBJECT_STORAGE=false
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_USE_SSL=false
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
RAW_BUCKET=raw
SLIDES_BUCKET=meeting-slides

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501

# Optional LLM provider
# OPENAI_API_KEY=...
# OPENAI_MODEL=gpt-4o-mini
```

**frontend/.env**
```ini
BACKEND_BASE_URL=http://127.0.0.1:8000
DEFAULT_UPLOAD_DIR=./samples
```

---

## 15) Legacy (superseded)

Old commands kept for reference:
- API (local): `uvicorn app.main:app --app-dir backend --reload --port 8000`
- Web (local): `streamlit run frontend/streamlit_app.py --server.port 3000`
- Separate workers (manual): replaced by **RQ** via `/v1/meetings/{id}/process`.

Use the queue flow in §3 going forward.
