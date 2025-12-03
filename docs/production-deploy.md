> Note: Throughout this doc, `https://notes.example.com` is a placeholder for
> your real production hostname. In local development, use `http://localhost:8000`
> instead.

# Production deployment

This document describes one concrete way to run Meeting Notes Assistant in a
small production environment using Docker Compose, Postgres, Redis, RQ worker,
MinIO, Prometheus, Grafana, and a reverse proxy/TLS terminator (e.g., Traefik).

The goal is a single, repeatable recipe you can follow on any new host.

## Prerequisites

- Linux host or VM with:
  - Docker and Docker Compose installed.
  - A DNS name pointing at the host (e.g., `notes.example.com`).
- TLS termination via Traefik or another reverse proxy.
- Access to:
  - A Postgres data volume or external Postgres instance.
  - A persistent volume for MinIO.
- A set of secrets (see below) stored outside Git:
  - API key(s).
  - DB password / URL.
  - MinIO credentials.
  - Redis password (optional but recommended).

## Environment configuration

Create or edit an environment file (e.g., `.env.production`) in the repo root.
At minimum you will need:

```bash
APP_ENV=production

# Postgres
DATABASE_URL=postgresql+psycopg://mna:<DB_PASSWORD>@db:5432/mna

# Redis / RQ
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=<MINIO_ACCESS_KEY>
MINIO_SECRET_KEY=<MINIO_SECRET_KEY>
MINIO_BUCKET=mna-meetings

# API auth
MNA_API_KEY=<your-long-random-api-key>

# Misc
LOG_LEVEL=info
