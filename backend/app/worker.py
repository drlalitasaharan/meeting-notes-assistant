# backend/app/worker.py
import os
import signal
import sys

from rq import Connection, Queue, Worker

from .jobs.queue import get_redis


def main():
    redis_conn = get_redis()
    queues = [q.strip() for q in os.getenv("RQ_WORKER_QUEUES", "default").split(",")]
    with Connection(redis_conn):
        worker = Worker([Queue(q) for q in queues])

        def handle_sig(signum, frame):
            worker.log.warning("Shutting down worker...")
            worker.request_stop()

        signal.signal(signal.SIGTERM, handle_sig)
        signal.signal(signal.SIGINT, handle_sig)

        worker.work(with_scheduler=True)


if __name__ == "__main__":
    sys.exit(main())
