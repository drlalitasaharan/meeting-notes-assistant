import logging
import sys

LOG_LEVEL = logging.getLevelName("INFO")

def configure_logging(level: str | int = LOG_LEVEL) -> None:
    """
    Configure application-wide logging.
    - INFO default, DEBUG in dev
    - Timestamps, module name, level
    """
    root = logging.getLogger()
    if root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s %(levelname)s %(name)s - %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    root.addHandler(handler)
    root.setLevel(level)

    # quiet noisy libs
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("minio").setLevel(logging.INFO)

