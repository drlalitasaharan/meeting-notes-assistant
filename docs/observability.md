# Observability – Health, Logs, and Metrics

This document describes how we observe the health and behavior of the Meeting Notes Assistant (MNA) system.

Core pillars:

- **Health checks** – quick “is it up?” checks for API, DB, queue, and storage.
- **Logs** – structured logs for requests and background jobs.
- **Metrics (lightweight)** – timings and counts emitted via logs, optionally exported to a metrics system later.
- **CI integration** – health and logs captured during automated tests.

---

## 1. Health checks

### 1.1 `/healthz` endpoint

The API exposes a health endpoint:

- `GET /healthz`

Example response:

```json
{
  "status": "ok",
  "checks": {
    "db": "ok",
    "redis": "ok",
    "storage": "ok",
    "worker_queue_len": 0
  }
}
