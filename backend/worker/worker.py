import os

import redis
from rq import Connection, Queue, Worker

from worker.redis_client import get_redis

r = get_redis()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("RQ_QUEUE", "default")

listen = [QUEUE_NAME]
conn = redis.from_url(REDIS_URL)

if __name__ == "__main__":
    with Connection(conn):
        Worker(list(map(Queue, listen))).work(with_scheduler=True)
