"""Note strategy package.

Keep package imports lightweight so utility modules can import concrete strategy
types without eagerly loading factory/local_summary and creating circular imports.
"""

from __future__ import annotations

from typing import Any


def get_notes_strategy(*args: Any, **kwargs: Any) -> Any:
    """Lazy compatibility wrapper for package-level imports."""
    from app.services.note_strategies.factory import (
        get_notes_strategy as _get_notes_strategy,
    )

    return _get_notes_strategy(*args, **kwargs)


__all__ = ["get_notes_strategy"]
