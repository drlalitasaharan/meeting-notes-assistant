# Meeting Notes Assistant — Frontend

## Overview
Streamlit (or lightweight Python UI) frontend for the **Meeting Notes Assistant** to exercise the end‑to‑end flow:
- Create a meeting
- Upload one or more slide files
- Trigger processing
- View/download transcript & summary artifacts

## Prerequisites
- Python 3.11+
- Backend running locally (`http://127.0.0.1:8000` by default)
- (Optional) Docker & Docker Compose to run the frontend container

## Quickstart (Docker Compose)
```bash
# from repo root
cp frontend/.env.example frontend/.env
# edit BACKEND_BASE_URL if needed

docker compose up -d frontend
```
Then open the exposed port from your compose file (commonly `http://127.0.0.1:3000` or Streamlit default `8501`).

## Quickstart (Local Python)
```bash
# from repo root
python -m venv .venv && source .venv/bin/activate
pip install -r frontend/requirements.txt

# configure env
cp frontend/.env.example frontend/.env
# edit BACKEND_BASE_URL as needed (defaults to http://127.0.0.1:8000)

# run the app (Streamlit)
streamlit run frontend/streamlit_app.py --server.port 3000
# or if app entry is a simple script
# python frontend/app.py
```

## Configuration
Create `frontend/.env` like:
```ini
# Where the backend API is reachable
BACKEND_BASE_URL=http://127.0.0.1:8000

# Optional: default upload folder for convenience
DEFAULT_UPLOAD_DIR=./samples
```

## Using the UI (typical flow)
1. **Create Meeting** → Calls `POST /v1/meetings` (or `/v1/meetings/start`) and returns an ID.
2. **Attach Slides** → Upload 1..N files using the `files` field to `POST /v1/meetings/{id}/slides`.
3. **Process** → Triggers `POST /v1/meetings/{id}/process` to run ASR/OCR/summarization.
4. **Results** → UI fetches transcript/summary endpoints (see backend docs) and offers downloads.

## Troubleshooting
- **CORS errors**: ensure backend `CORS_ORIGINS` includes your frontend origin (e.g., `http://localhost:3000`).
- **Uploads fail**: make sure the form field is named `files` and the backend has access to MinIO (`MINIO_ENDPOINT` etc.).
- **Cannot connect to backend**: verify `BACKEND_BASE_URL` and that `http://127.0.0.1:8000/healthz` returns `{status: ok}`.

## Project Layout (frontend)
```
frontend/
  streamlit_app.py   # main UI (current)
  app.py             # optional lightweight entry
  components/        # shared UI bits
  requirements.txt
  .env.example
```

## Sample `.env.example` files
**backend/.env.example**
```ini
APP_ENV=dev
PORT=8000
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./dev.db
# DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/meetings
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_USE_SSL=false
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
RAW_BUCKET=raw
SLIDES_BUCKET=meeting-slides
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501
```

**frontend/.env.example**
```ini
BACKEND_BASE_URL=http://127.0.0.1:8000
DEFAULT_UPLOAD_DIR=./samples
```

## License
Internal/MVP. Replace with your preferred license for distribution.
