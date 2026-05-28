# backend/app/jobs/queue.py
import os

from redis import Redis
from rq import Queue


def get_redis() -> Redis:
    """
    Prefer REDIS_URL in hosted environments like Render.
    Fall back to REDIS_HOST/REDIS_PORT/REDIS_DB for local Docker/dev.
    """
    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url:
        return Redis.from_url(redis_url)

    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return Redis(host=host, port=port, db=db)


def get_queue(name: str | None = None) -> Queue:
    qname = name or "default"
    return Queue(qname, connection=get_redis())


# Default RQ queue used by jobs that import `queue`
queue = get_queue("default")
