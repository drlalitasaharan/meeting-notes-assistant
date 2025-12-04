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

### Checking metrics locally

To confirm that the API is exposing Prometheus metrics, run:

curl -f http://localhost:8000/metrics-prom | head

You should see Prometheus-style text output (starting with '# HELP' / '# TYPE') and counters like 'http_requests_total' and histograms like 'http_request_duration_seconds'. In production, Prometheus should scrape the backend at '/metrics-prom' (for example 'http://backend:8000/metrics-prom' on the Docker network, or 'https://notes.example.com/metrics-prom' via your reverse proxy).

## Alerts and runbooks

### Where the alert rules live

Prometheus alerting rules are checked into the repo at:

- `prometheus/alerts.yml`

They are loaded from `prometheus.yml` via:

```yaml
rule_files:
  - "prometheus/alerts.yml"

```

When you update alerts, remember to reload Prometheus (or restart the container) so changes take effect.

### API errors and latency

Related alerts:

- `Api5xxRateHigh`
- `ApiLatencyHigh`

First steps when these fire:

1. **Check Grafana “MNA – Golden Flow” dashboard:**
   - Look at:
     - **HTTP request rate by status (api)** – is 5xx spiking?
     - **HTTP latency P95/P99 (api)** – is latency high at the same time?
2. **Check `/healthz`:**
   - `curl -f http://backend:8000/healthz` or via the reverse proxy.
   - If `/healthz` fails, the problem is likely DB/Redis/MinIO or the app itself.
3. **Check logs:**
   - API logs around the time of the alert.
   - Worker logs if failures involve the real MVP path (`process_meeting`).
4. **Look for recent changes:**
   - New deploys, config changes, schema migrations.
5. **If DB-bound:**
   - Look for slow queries, locks, or connection exhaustion.
   - Check for high CPU or I/O on the DB host.

### RQ job failures and backlog

Related alerts:

- `RQJobFailuresHigh`
- `RQQueueBacklogHigh`

First steps when these fire:

1. **Check Grafana:**
   - **RQ jobs enqueued/completed/failed (rate, all queues)** – is `failed` spiking?
   - **Failed jobs (last 15m, by job_name)** – which `job_name` is failing?
   - **RQ queue depth (by queue)** and **RQ backlog proxy** – is there a backlog?
2. **Inspect worker logs:**
   - Use `job_name`, `queue`, and `job_id` from the metrics panel.
   - Check structured logs from `ObservabilityWorker` for stack traces and context.
3. **Look for systemic issues:**
   - Broken external dependencies (e.g., ASR/OCR services).
   - Schema changes that made existing jobs invalid.
4. **Mitigation options:**
   - Temporarily pause traffic or enqueueing if needed.
   - Fix the underlying bug and redeploy.
   - Manually re-queue or clean up failed jobs once fixed.

### Worker down

Related alert:

- `RQWorkerDown`

First steps when this fires:

1. **Check Grafana “Service health (up)” panel:**
   - Confirm `up{job="worker"}` is `0`.
2. **Check the container:**
   - `./bin/dc ps` – is the `worker` container unhealthy or restarting?
   - `./bin/dc logs worker` – look for tracebacks, config errors, OOM kills.
3. **Check dependencies:**
   - Redis health (`./bin/dc logs redis`, `/healthz`).
   - If Redis is down, worker won’t be able to fetch jobs.
4. **Mitigate:**
   - Fix the underlying cause (config, code, resource limits).
   - Restart the worker: `./bin/dc up -d worker`.
5. **After recovery:**
   - Watch queue depth and job failure panels to ensure the backlog drains cleanly.
