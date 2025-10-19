# backend/app/jobs/pipeline.py — minimal, mypy-friendly scaffold

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy.orm import Session

from app.core.db import SessionLocal


# --- lightweight metrics (no prometheus needed) ---
class _Noop:
    def labels(self, *_, **__):
        return self

    def inc(self, *_, **__):
        pass

    def observe(self, *_, **__):
        pass

    def time(self):
        class _Ctx:
            def __enter__(self):
                return None

            def __exit__(self, *_):
                return False

        return _Ctx()


# Exported metrics used elsewhere
JOB_DUR: Any = _Noop()
JOB_COUNT: Any = _Noop()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Canonical DB session lifecycle."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


__all__ = ["JOB_DUR", "JOB_COUNT", "session_scope"]


def process_meeting(*args, **kwargs) -> None:
    """Stubbed pipeline hook (no-op)."""
    return
