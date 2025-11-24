# Meeting Notes Assistant – Operations Runbook

This runbook explains how to operate the Meeting Notes Assistant (MNA) in production-like environments.

Stack (high-level):

- API: FastAPI (`backend/app`)
- DB: Postgres
- Queue: Redis + RQ worker
- Object store: MinIO/S3
- CI: GitHub Actions (build, smoke, lint/test)
- Reverse proxy / TLS (if enabled): Traefik

Assumptions:

- Commands are run from the repo root.
- You have Docker and `docker compose` installed.
- The main compose files are:
  - `docker-compose.yml`
  - `docker-compose.prodready.yml`
  - (Optionally additional overlays for local dev/CI)

---

## 1. How to check system health

### 1.1 Health endpoint

The API exposes a health endpoint:

- URL (local): `http://127.0.0.1:8000/healthz`
- URL (behind Traefik, local): `https://api.mna.local/healthz` (if using TLS/local DNS)

Example (local):

```bash
curl -s http://127.0.0.1:8000/healthz | jq .

(.venv) (base) lalitasaharan@C02DD2LQML7L meeting-notes-assistant % cd ~/Code/AJENCEL/meeting-notes-assistant
git status
ls .github/workflows

On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
ci.yml          lint.yml        smoke.yml
(.venv) (base) lalitasaharan@C02DD2LQML7L meeting-notes-assistant % >....
Assumptions:

- Commands are run from the repo root.
- You have Docker and `docker compose` installed.
- The main compose files are:
  - `docker-compose.yml`
  - `docker-compose.prodready.yml`
  - (Optionally additional overlays for local dev/CI)

---

## 1. How to check system health

### 1.1 Health endpoint

The API exposes a health endpoint:

- URL (local): `http://127.0.0.1:8000/healthz`
- URL (behind Traefik, local): `https://api.mna.local/healthz` (if using TLS/local DNS)

Example (local):

```bash
curl -s http://127.0.0.1:8000/healthz | jq .

## MP4 → Transcript → AI Notes → Markdown

This is the main “golden flow” for Meeting Notes Assistant: take a meeting recording (MP4), turn it into a transcript, generate AI-powered notes, and expose the output as both JSON and downloadable markdown.

### High-level flow

1. **Create a meeting**
   - Client calls `POST /v1/meetings` with a title and optional tags.
   - Backend creates a `meetings` row in Postgres.

2. **Upload MP4**
   - Client calls `POST /v1/meetings/{id}/upload` with the MP4 file.
   - Backend stores the raw media via `_save_raw_media_stub` in dev/tests (in prod this is swapped to real object storage).
   - Backend enqueues an RQ job `process_meeting(meeting_id=...)` and returns a JSON envelope including the `job_id`.

3. **Background processing (RQ worker)**
   - The RQ worker listens on the same Redis queue as the API.
   - For each job, `process_meeting(meeting_id=...)`:
     - Fetches the meeting + media location.
     - Runs ASR to generate a **transcript**.
     - Runs the AI notes pipeline to produce structured **AI notes**.
     - Persists notes in the `meeting_notes` table and renders a **markdown** version.

4. **Read AI notes / markdown**
   - `GET /v1/meetings/{id}/notes/ai` returns the structured AI notes as JSON.
   - `GET /v1/meetings/{id}/notes.md` returns the markdown version (for download, previews, etc.).

### Endpoints involved

- `POST /v1/meetings` – create a meeting.
- `POST /v1/meetings/{id}/upload` – upload MP4, enqueue processing job.
- `GET /v1/meetings/{id}/notes/ai` – fetch AI notes (JSON).
- `GET /v1/meetings/{id}/notes.md` – fetch AI notes (markdown).

The main background job is:

- `process_meeting(meeting_id: int)` in `app.jobs.meetings`, which is invoked asynchronously via RQ (and can still be called directly in tests).

### How to try this locally

Assuming you have Redis, Postgres, the API, and the worker running (via Docker Compose or your usual dev setup):

1. **Create a meeting**

   ```bash
   http POST :8000/v1/meetings \
     title="Demo planning sync" \
     tags="demo,notes"
