# backend/worker/worker.py
import os

from redis import Redis
from rq import Queue, Worker


def get_redis() -> Redis:
    """
    Use REDIS_URL in hosted environments like Render.
    Fall back to local Docker Redis for development.
    """
    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url:
        return Redis.from_url(redis_url)

    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return Redis(host=host, port=port, db=db)


def main() -> None:
    redis_conn = get_redis()
    queue_name = os.getenv("RQ_QUEUE", "default")
    queue = Queue(queue_name, connection=redis_conn)

    worker = Worker([queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
