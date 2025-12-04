# Grafana dashboards

## MNA – Golden Flow dashboard

This dashboard focuses on the Real MVP golden flow:

> `Create meeting → upload MP4 → RQ/Redis → process_meeting → meeting_notes row in Postgres`

### Importing the dashboard

1. In Grafana, go to **Dashboards → New → Import**.
2. Either:
   - Paste the JSON from `docs/grafana/mna-golden-flow.json`, **or**
   - Upload the file directly.
3. When prompted, select your **Prometheus** datasource (or map `PROMETHEUS_DS` to the correct one).
4. Click **Import**.

### Panels and how to use them

#### HTTP request rate by status / path

- **Panels:**
  - `HTTP request rate by status (api)`
  - `HTTP request rate by path (api)`
- **Queries:**
  - `sum by (status) (rate(http_requests_total{service="api"}[5m]))`
  - `topk(10, sum by (path) (rate(http_requests_total{service="api"}[5m])))`
- **Use when:**
  - You suspect **lots of errors** or unusual traffic patterns.
  - Debugging "**lots of 5xx errors**".
- **Typical flow:**
  - If the 5xx series spikes, check:
    - Recent deploys/config changes.
    - `/healthz` and application logs.
    - DB/Redis/MinIO health if 5xx correlate with dependency issues.

#### HTTP latency P95/P99

- **Panel:** `HTTP latency P95/P99 (api)`
- **Queries:**
  - `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{service="api"}[5m])))`
  - `histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{service="api"}[5m])))`
- **Use when:**
  - Investigating "**Real MVP is slow**".
- **Typical flow:**
  - If P95/P99 latency rises:
    - Check DB load (slow queries, locks).
    - Check Redis/MinIO latency or network issues.
    - Look for spikes in request rate.
    - Compare with RQ job throughput: slow jobs might block resources.

#### RQ jobs: throughput & failures

- **Panels:**
  - `RQ jobs enqueued/completed/failed (rate, all queues)`
  - `Failed jobs (last 15m, by job_name)`
- **Queries:**
  - `sum by (queue) (rate(mna_jobs_enqueued_total[5m]))`
  - `sum by (queue) (rate(mna_jobs_completed_total[5m]))`
  - `sum by (queue) (rate(mna_jobs_failed_total[5m]))`
  - `sum by (job_name) (increase(mna_jobs_failed_total[15m]))`
- **Use when:**
  - Debugging "**jobs are stuck**" or "**lots of job failures**".
- **Typical flow:**
  - If `failed` lines spike or the failed-jobs panel highlights a job:
    - Grab `job_name` and `queue`.
    - Use worker logs (structured logs with `job_id`, `queue`, `job_name`) to find root cause.
    - Check if a recent deploy broke the job's code or dependencies.

#### Queue health & backlog

- **Panels:**
  - `RQ queue depth (by queue)`
  - `RQ backlog proxy (enqueued - completed rate, default queue)`
- **Queries:**
  - `sum by (queue) (mna_jobs_queue_depth)`
  - `sum(rate(mna_jobs_enqueued_total{queue="default"}[5m])) - sum(rate(mna_jobs_completed_total{queue="default"}[5m]))`
- **Use when:**
  - Debugging "**jobs are stuck**" or slow note generation.
- **Typical flow:**
  - If `queue_depth` stays high and backlog rate is positive:
    - Check `RQ worker` container health.
    - Look for very slow jobs (long processing time).
    - Consider scaling workers or splitting queues.

#### Worker / service health

- **Panel:** `Service health (up)`
- **Query:** `sum by (job) (up{job=~"api|worker"})`
- **Use when:**
  - Checking if the **api** or **worker** Prometheus target is up.
- **Typical flow:**
  - If `up{job="worker"}` or `up{job="api"}` drops:
    - Check `./bin/dc ps` and `./bin/dc logs <service>`.
    - Verify container restarts, OOM kills, or crash loops.
