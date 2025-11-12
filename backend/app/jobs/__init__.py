import os
from functools import lru_cache

from redis import Redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


@lru_cache(maxsize=1)
def get_connection() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=False)


@lru_cache(maxsize=1)
def get_queue() -> Queue:
    return Queue("default", connection=get_connection())
