from __future__ import annotations

import logging
from typing import Any, Callable, Union

from rq import Queue
from rq.job import Job

from app.metrics import JOBS_ENQUEUED

log = logging.getLogger(__name__)

FuncOrStr = Union[Callable[..., Any], str]


def enqueue_with_metrics(
    queue: Queue,
    func: FuncOrStr,
    *args: Any,
    service: str = "api",
    **kwargs: Any,
) -> Job:
    """
    Enqueue an RQ job and increment the Prometheus counter.

    `func` can be a callable or a string path
    (e.g. "worker.tasks.demo_job").

    Extra *args / **kwargs are passed directly to `queue.enqueue(...)`.
    """
    job: Job = queue.enqueue(func, *args, **kwargs)

    try:
        if hasattr(job, "func_name"):
            # RQ often sets job.func_name for both callables and strings
            job_name = job.func_name  # type: ignore[attr-defined]
        elif isinstance(func, str):
            job_name = func
        else:
            job_name = getattr(func, "__name__", "unknown")

        JOBS_ENQUEUED.labels(
            queue=queue.name,
            job_name=job_name,
            service=service,
        ).inc()
    except Exception:
        # Metrics must never break the request path
        log.exception(
            "Failed to increment JOBS_ENQUEUED",
            extra={"queue": queue.name, "job_id": getattr(job, "id", None)},
        )

    return job
