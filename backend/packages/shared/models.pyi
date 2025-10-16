from datetime import datetime
from typing import Any

class _Base:
    id: Any
    created_at: datetime
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class Meeting(_Base):
    title: Any
    tags: Any
    status: Any

class Transcript(_Base):
    meeting_id: Any
    text: str

class Summary(_Base):
    meeting_id: Any
    text: str | None
    bullets: str

class Slide(_Base):
    meeting_id: Any
    page_num: int
    ocr_text: str | None
    storage_key: str
