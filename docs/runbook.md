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

heredoc>
