from __future__ import annotations


def tiny_job(x: int) -> int:
    """Tiny RQ job used for Redis/worker smoke tests."""
    return x * 2
