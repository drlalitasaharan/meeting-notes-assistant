from datetime import datetime
from typing import Any

class _Base:
    id: Any
    created_at: datetime
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class Transcript(_Base):
    meeting_id: Any
    text: str

class Summary(_Base):
    meeting_id: Any
    text: str | None
    bullets: str
