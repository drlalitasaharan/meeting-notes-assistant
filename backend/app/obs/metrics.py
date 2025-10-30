from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter("http_requests_total", "HTTP requests", ["path", "method", "status"])

JOB_COUNT = Gauge("job_count_by_status", "Jobs by status (type/status)", ["type", "status"])

JOB_DURATION = Histogram(
    "job_duration_seconds",
    "Job durations (by type)",
    ["type"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600),
)
