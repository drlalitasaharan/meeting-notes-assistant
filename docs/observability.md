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

### Optional: Grafana dashboards (jobs + worker)

If you have Prometheus and Loki wired up, you can create a small “Jobs & Worker Observability” dashboard with 3–4 panels built on:

- **Prometheus metrics**: `mna_jobs_enqueued_total`, `mna_jobs_completed_total`, `mna_jobs_failed_total`
- **Labels** (typical): `job_name`, `queue`
- **Loki labels**: `service`, `job_id`, `job_name`, `queue`, `level`, `route`, etc.

#### Suggested dashboard: “Jobs & Worker Observability”

**Template variables**

These make it easier to slice by job / queue:

- **`$job_name`**
  - Data source: Prometheus
  - Query:
    ```promql
    label_values(mna_jobs_enqueued_total, job_name)
    ```

- **`$queue`**
  - Data source: Prometheus
  - Query:
    ```promql
    label_values(mna_jobs_enqueued_total, queue)
    ```

You can mark both as “All” by default.

---

#### Panel 1 – Job throughput by type (5m rate)

- **Goal:** “Are jobs flowing through the system? Which job types are busiest?”
- **Type:** Time series
- **Data source:** Prometheus
- **Query (per job_name):**
  ```promql
  sum by (job_name) (
    rate(mna_jobs_enqueued_total{queue=~"$queue"}[5m])
  )
