# backend/app/metrics.py
import time

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
REQ_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "path"]
)


def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    resp = await call_next(request)
    dur = time.perf_counter() - start
    try:
        path = request.url.path
        REQ_DURATION.labels(request.method, path).observe(dur)
        REQUESTS.labels(request.method, path, str(resp.status_code)).inc()
    except Exception:
        pass
    return resp
