from __future__ import annotations

import os
import sys
import time

import redis
from rq import Queue

from app.jobs.smoke_tasks import tiny_job

REDIS_URL = os.getenv("REDIS_URL", "")
QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "default")
SMOKE_TIMEOUT_SECS = float(os.getenv("RQ_SMOKE_TIMEOUT", "20.0"))


def main() -> int:
    if not REDIS_URL:
        # For dev/tests where Redis isn't configured, treat as a no-op success.
        print("REDIS_URL not set; skipping RQ smoke check", file=sys.stderr)
        return 0

    conn = redis.from_url(REDIS_URL)
    q = Queue(QUEUE_NAME, connection=conn)

    job = q.enqueue(tiny_job, 21, job_timeout=SMOKE_TIMEOUT_SECS)
    print(f"Enqueued RQ smoke job {job.id} on queue={QUEUE_NAME}")

    deadline = time.time() + SMOKE_TIMEOUT_SECS

    while time.time() < deadline:
        # Re-fetch the job from Redis using the queue helper
        refreshed = q.fetch_job(job.id)
        if refreshed is None:
            print(
                f"Job {job.id} not found in queue/Redis anymore",
                file=sys.stderr,
            )
            return 1

        status = refreshed.get_status()
        print(f"Job {job.id} status={status!r}")

        if status == "finished":
            if refreshed.result != 42:
                print(
                    f"Unexpected job result: {refreshed.result!r} (expected 42)",
                    file=sys.stderr,
                )
                return 1
            print("RQ smoke job completed successfully with result=42")
            return 0

        if status in {"failed", "stopped", "canceled"}:
            print(f"RQ smoke job ended in bad state: {status}", file=sys.stderr)
            return 1

        time.sleep(0.5)

    print("Timeout waiting for RQ smoke job to finish", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
