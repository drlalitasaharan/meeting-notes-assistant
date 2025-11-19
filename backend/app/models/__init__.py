from __future__ import annotations

from typing import Any

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Import ORM models so that their tables are registered on Base.metadata.
# This ensures Base.metadata.create_all() sees jobs, meetings, meeting_notes, etc.
from app.models import job as _job  # noqa: F401,E402
from app.models import meeting as _meeting  # noqa: F401,E402
from app.models import meeting_notes as _meeting_notes  # noqa: F401,E402

Transcript = Any  # type: ignore[misc]
Summary = Any  # type: ignore[misc]
