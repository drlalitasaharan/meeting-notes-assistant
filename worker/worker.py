from __future__ import annotations

import logging
import os
import sys
from typing import Sequence

from redis import Redis
from rq import Connection, Queue, Worker

# Make sure backend/app is importable as "app"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.logging_utils import (  # type: ignore[import]  # noqa: E402
    bind_job_context,
    configure_logging,
    get_logger,
    log_kv,
)

listen_queues = ["default", "failed"]

# Configure structured logging for the worker process
configure_logging("worker")
logger = get_logger(__name__)


def get_redis_url() -> str:
    """
    Redis URL for the worker.

    Defaults to the docker-compose redis service, but can be overridden
    via REDIS_URL.
    """
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


class ObservabilityWorker(Worker):
    """
    RQ Worker that attaches job context and logs lifecycle events.
    """

    def execute_job(self, job, queue, *args, **kwargs):
        # Attach job_id to the logging context for the duration of the job
        bind_job_context(job.id)
        queue_name = getattr(queue, "name", "default")

        log_kv(
            logger,
            logging.INFO,
            "job starting",
            job_id=job.id,
            queue=queue_name,
        )

        try:
            result = super().execute_job(job, queue, *args, **kwargs)
        except Exception:
            logger.exception(
                "job failed",
                extra={"job_id": job.id, "queue": queue_name},
            )
            raise
        else:
            log_kv(
                logger,
                logging.INFO,
                "job completed",
                job_id=job.id,
                queue=queue_name,
            )
            return result


def main() -> None:
    """
    Entry point for `python -m worker.worker`.
    """
    redis_url = get_redis_url()
    conn = Redis.from_url(redis_url)

    with Connection(conn):
        queues: Sequence[Queue] = [Queue(name) for name in listen_queues]

        logger.info(
            "worker starting",
            extra={
                "queues": [q.name for q in queues],
                "redis_url": redis_url,
            },
        )

        worker = ObservabilityWorker(queues)
        # Keep scheduler behaviour the same as before
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
