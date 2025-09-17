# app/core/logger.py
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Attach any extra fields passed via logger.info("msg", extra={"foo": "bar"})
        for k, v in record.__dict__.items():
            if k not in payload and k not in ("args", "msg", "levelno", "levelname",
                                              "pathname", "filename", "created", "msecs",
                                              "relativeCreated", "thread", "threadName",
                                              "processName", "process", "stack_info",
                                              "exc_text", "exc_info", "name"):
                payload[k] = v
        return json.dumps(payload, ensure_ascii=False)

def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    # Clear old handlers (important if reloading)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

