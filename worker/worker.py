from __future__ import annotations
import os
import sys
from rq import Worker, Queue, Connection
from redis import Redis

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

listen_queues = ["default", "failed"]


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker(list(map(Queue, listen_queues)))
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
