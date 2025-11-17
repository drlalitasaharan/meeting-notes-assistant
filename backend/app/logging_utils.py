from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)


class JsonFormatter(logging.Formatter):
    """Very small JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        req_id = _request_id_ctx.get()
        job_id = _job_id_ctx.get()

        if req_id:
            payload["request_id"] = req_id
        if job_id:
            payload["job_id"] = job_id

        # Attach any custom extras passed via `extra={...}`
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "process",
                "processName",
            }:
                continue
            if key in payload:
                continue
            payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(service: str) -> None:
    """
    Configure root logging for API / worker.

    Call once at process start, e.g.:

        configure_logging("api")
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    # Make uvicorn logs structured but not too noisy.
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    # Tag service in all logs via LoggerAdapter if needed later
    root.info("logging configured", extra={"service": service})


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)


def bind_request_context(request_id: str | None) -> None:
    _request_id_ctx.set(request_id)


def bind_job_context(job_id: str | None) -> None:
    _job_id_ctx.set(job_id)


def log_kv(
    logger: logging.Logger,
    level: int,
    message: str,
    **fields: Any,
) -> None:
    """
    Convenience helper:

        log_kv(logger, logging.INFO, "queue job", job_id=job.id, queue=job.origin)
    """
    logger.log(level, message, extra=fields)
